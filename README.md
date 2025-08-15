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
