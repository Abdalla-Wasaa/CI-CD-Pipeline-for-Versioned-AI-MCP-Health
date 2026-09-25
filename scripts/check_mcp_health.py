import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402
from mcp.client.streamable_http import streamablehttp_client  # noqa: E402
from check_prompt_pin import ROOT, validate  # noqa: E402


async def inspect(read, write):
    async with ClientSession(read, write) as session:
        hello = await session.initialize()
        if hello.serverInfo.version != validate()[0]["mcp_version"]:
            raise ValueError("MCP server version mismatch")
        names = {tool.name for tool in (await session.list_tools()).tools}
        if not {"check_stock"}.issubset(names):
            raise ValueError("Missing required tool")
        resources = {str(r.uri) for r in (await session.list_resources()).resources}
        if "clinics://directory" not in resources:
            raise ValueError("Missing required resource")
        resource = await session.read_resource("clinics://directory")
        if not json.loads(resource.contents[0].text)["clinics"]:
            raise ValueError("Empty clinic directory")
        result = await session.call_tool("check_stock", {"item": "ors_sachets"})
        if result.isError:
            raise ValueError("Tool execution failed")
        return {"status": "PASS", "mcp_version": hello.serverInfo.version,
                "protocol": hello.protocolVersion, "tools": sorted(names)}


async def check(url=None, server=ROOT / "logistics_mcp_versioned.py"):
    async with asyncio.timeout(20):
        if url:
            async with streamablehttp_client(url) as (read, write, _):
                return await inspect(read, write)
        async with stdio_client(StdioServerParameters(command=sys.executable,
                                args=[str(server)])) as (read, write):
            return await inspect(read, write)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Live Streamable HTTP MCP endpoint")
    parser.add_argument("--server", type=Path, default=ROOT / "logistics_mcp_versioned.py")
    args = parser.parse_args()
    try:
        print(json.dumps(asyncio.run(check(args.url, args.server))))
    except Exception as exc:
        print(f"FAIL MCP health: {exc}", file=sys.stderr)
        sys.exit(1)
