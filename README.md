# MCP Strava Server

A small Python MCP server that lets Claude Desktop read your Strava activities. Ask things like: show my last 10 runs with distance and average pace.

## What it does
- Tools: `oauth_login`, `list_activities`, `get_activity`
- Local OAuth with automatic token refresh
- Tokens saved to a local JSON file that is not committed

## Prereqs
- Windows 10 or 11 on x64
- Python 3.10 or newer
- Claude Desktop installed

## Setup
```powershell
cd C:\Users\AtikantJain\mcp-strava
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt


```mermaid
flowchart TD
    A[Start in VS Code] --> B[Write server.py with MCP tools and env based config]
    B --> C[Install deps in venv: mcp[cli], requests, anyio]
    C --> D[Strava app settings: Authorisation Callback Domain = localhost, Website = http://localhost]
    D --> E[In Claude Desktop add server env vars:<br>STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET,<br>STRAVA_REDIRECT_URI, STRAVA_TOKEN_PATH, STRAVA_SCOPES]
    E --> F[Claude launches MCP server via venv python and args server.py]
    F --> G{You run oauth_login in Claude}
    G --> H[Server starts local callback on http://localhost:8723/callback and opens browser]
    H --> I[You sign in to Strava and authorise]
    I --> J[Strava redirects back with code]
    J --> K[Server POST /oauth/token with client_id, client_secret, code]
    K --> |200 OK| L[Server saves access_token, refresh_token, expires_at to STRAVA_TOKEN_PATH]
    L --> M[You call list_activities or get_activity from Claude]
    M --> N{Is access_token expired soon}
    N -- Yes --> O[Server POST /oauth/token with refresh_token to get new tokens]
    O --> L
    N -- No --> P[Server calls Strava API with Authorization Bearer access_token]
    P --> Q[JSON returns to MCP server]
    Q --> R[Claude replies to you with a summary]

    %% Error branch during login
    K --> |401 or other error| S{Error type}
    S --> |client_secret invalid| T[Fix STRAVA_CLIENT_SECRET in Claude env then run oauth_login again]
    S --> |client_id invalid| U[Fix STRAVA_CLIENT_ID then run oauth_login again]
    S --> |redirect_uri mismatch| V[Keep STRAVA_REDIRECT_URI = http://localhost:8723/callback and dashboard domain = localhost]
    S --> |code invalid or expired| W[Run oauth_login again and authorise promptly]
```

