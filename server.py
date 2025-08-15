# server.py
import json
import os
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

import requests
from mcp.server.fastmcp import FastMCP

# ----- Configuration from environment -----

from dotenv import load_dotenv  # pip install python-dotenv
load_dotenv()

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID", "")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "")
STRAVA_REDIRECT_URI = os.getenv("STRAVA_REDIRECT_URI", "http://localhost:8723/callback")
TOKEN_PATH = os.getenv("STRAVA_TOKEN_PATH", "C:\\Users\\AtikantJain\\mcp-strava\\.strava_tokens.json")


STRAVA_BASE = "https://www.strava.com/api/v3"
AUTH_BASE = "https://www.strava.com/oauth"
SCOPES = "read,read_all,profile:read_all,activity:read_all"

mcp = FastMCP("strava")

# ----- Token helpers -----
def _load_tokens():
    try:
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _save_tokens(tok):
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(tok, f, indent=2)

def _refresh_token_if_needed() -> str:
    """
    Return a valid access token, refreshing if expired or close to expiry.
    """
    tokens = _load_tokens()
    if not tokens:
        raise RuntimeError("No tokens found. Run oauth_login first.")

    now = int(time.time())
    # refresh if token expires within next 2 minutes
    if now >= int(tokens.get("expires_at", 0)) - 120:
        resp = requests.post(
            f"{AUTH_BASE}/token",
            json={
                "client_id": STRAVA_CLIENT_ID,
                "client_secret": STRAVA_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": tokens["refresh_token"],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        tokens = {
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "expires_at": data["expires_at"],
        }
        _save_tokens(tokens)
    return tokens["access_token"]

# ----- OAuth handler -----
class _OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            q = parse_qs(urlparse(self.path).query)
            if "code" in q:
                code = q["code"][0]
                # Exchange code for tokens
                resp = requests.post(
                    f"{AUTH_BASE}/token",
                    json={
                        "client_id": STRAVA_CLIENT_ID,
                        "client_secret": STRAVA_CLIENT_SECRET,
                        "code": code,
                        "grant_type": "authorization_code",
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                tokens = {
                    "access_token": data["access_token"],
                    "refresh_token": data["refresh_token"],
                    "expires_at": data["expires_at"],
                }
                _save_tokens(tokens)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Strava authorisation complete. You can close this window.")
                # Stop server shortly after
                threading.Thread(target=self.server.shutdown, daemon=True).start()
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing code parameter.")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {e}".encode("utf-8"))

def _start_callback_server(port: int = 8723):
    httpd = HTTPServer(("localhost", port), _OAuthHandler)
    httpd.serve_forever()

# ----- MCP tools -----
@mcp.tool()
def oauth_login() -> str:
    """
    Open the browser to authorise Strava, then capture tokens at the local callback.
    Run this once. If you change scopes later, run again.
    """
    if not STRAVA_CLIENT_ID or not STRAVA_CLIENT_SECRET:
        return "Please set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET"

    # Start local callback server in a thread
    t = threading.Thread(target=_start_callback_server, daemon=True)
    t.start()

    auth_url = (
        f"{AUTH_BASE}/authorize"
        f"?client_id={STRAVA_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={STRAVA_REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&approval_prompt=force"
    )
    webbrowser.open(auth_url)
    return "Opened browser for Strava login. Approve access, then return here."

def _iso_or_epoch_to_epoch(value: int | str | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    # Accept "YYYY-MM-DD"
    try:
        import datetime as dt
        d = dt.datetime.strptime(value, "%Y-%m-%d")
        return int(d.replace(tzinfo=dt.timezone.utc).timestamp())
    except Exception:
        return None

@mcp.tool()
def list_activities(per_page: int = 10, page: int = 1, after: int | str | None = None, before: int | str | None = None):
    """
    List your activities. Optional filters:
    - per_page default 10
    - page default 1
    - after accepts epoch seconds or 'YYYY-MM-DD'
    - before accepts epoch seconds or 'YYYY-MM-DD'
    """
    token = _refresh_token_if_needed()
    params = {
        "per_page": per_page,
        "page": page,
    }
    aft = _iso_or_epoch_to_epoch(after)
    bef = _iso_or_epoch_to_epoch(before)
    if aft is not None:
        params["after"] = aft
    if bef is not None:
        params["before"] = bef

    resp = requests.get(f"{STRAVA_BASE}/athlete/activities", headers={"Authorization": f"Bearer {token}"}, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

@mcp.tool()
def get_activity(activity_id: int):
    """
    Get a single activity by id.
    """
    token = _refresh_token_if_needed()
    resp = requests.get(f"{STRAVA_BASE}/activities/{activity_id}", headers={"Authorization": f"Bearer {token}"}, timeout=30)
    resp.raise_for_status()
    return resp.json()

# Entry point for Claude and for local testing
# --- keep everything above as is ---

# Keep all your imports and tool definitions above

if __name__ == "__main__":
    import sys
    # Only write human logs to stderr, never stdout
    print("Booting Strava MCP server...", file=sys.stderr)
    from mcp.server.fastmcp import FastMCP  # already imported above in your file
    # This blocks correctly when Claude launches the server over stdio
    mcp.run()


