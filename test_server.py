from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server
import anyio

mcp = FastMCP("strava")

@mcp.tool()
def ping() -> dict:
    "Simple connectivity test"
    return {"status": "ok"}

async def _main():
    async with stdio_server() as (read, write):
        await mcp.run(read, write)

if __name__ == "__main__":
    print("Starting MCP ping server on stdio...")
    anyio.run(_main)
