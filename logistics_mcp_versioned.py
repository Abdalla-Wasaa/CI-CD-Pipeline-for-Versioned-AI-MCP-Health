import json
import os

from mcp.server.fastmcp import FastMCP

from check_prompt_pin import ROOT, validate

VERSION = validate()[0]["mcp_version"]
mcp = FastMCP("afyaplus-logistics", host="127.0.0.1")
# FastMCP 1.x exposes protocol serverInfo via its underlying server.
mcp._mcp_server.version = VERSION


@mcp.tool()
def check_stock(item: str) -> dict:
    """Return synthetic stock counts; never access real patient information."""
    clinics = json.loads((ROOT / "clinics.json").read_text())["clinics"]
    return {"item": item, "stock": [{"clinic": c["id"], "units": c["stock"].get(item, 0)}
                                    for c in clinics]}


@mcp.resource("clinics://directory")
def clinic_directory() -> str:
    """Return the synthetic clinic directory."""
    return (ROOT / "clinics.json").read_text()


if __name__ == "__main__":
    mcp.run(transport=os.environ.get("MCP_TRANSPORT", "stdio"))
