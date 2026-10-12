"""Read-only runtime checks; execute this file inside the Goofish container."""
from __future__ import annotations

import argparse
import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from goofish_cli.core.browser import goofish_page


async def verify(require_login=False):
    async with goofish_page(cookies={}) as page:
        await page.set_content("<title>Goofish Docker check</title>")
        if await page.title() != "Goofish Docker check":
            raise RuntimeError("Chrome 页面检查失败")
    print("Chrome + Xvfb: OK", flush=True)
    params = StdioServerParameters(command="goofish-cli", env=dict(os.environ))
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        names = {tool.name for tool in tools.tools}
        if not {"auth_status", "search_items", "item_get"}.issubset(names):
            raise RuntimeError("MCP 工具清单不完整")
        print(f"MCP: OK ({len(names)} tools)", flush=True)
        if require_login:
            result = await session.call_tool("auth_status", {})
            payload = result.structuredContent or {}
            if result.isError or not payload.get("ok") or not payload.get("data", {}).get("valid"):
                raise RuntimeError("闲鱼登录未确认有效，请重新导入 Chrome 登录态")
            print("Goofish login: valid", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-login", action="store_true")
    args = parser.parse_args()
    asyncio.run(verify(args.require_login))
