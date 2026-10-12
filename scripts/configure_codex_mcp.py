#!/usr/bin/env python3
"""Register Docker-backed Goofish MCP without replacing other Codex settings."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path


def parse_toml(text):
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    return tomllib.loads(text)


def configure(config_path: Path, docker_command: str) -> str:
    original = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    data = parse_toml(original)
    servers = data.get("mcp_servers", {})
    args = ["exec", "-i", "goofish-cli", "goofish-cli"]
    expected = {
        "command": docker_command,
        "args": args,
        "startup_timeout_sec": 30,
        "tool_timeout_sec": 180,
        "default_tools_approval_mode": "prompt",
        "disabled_tools": ["auth_login", "auth_reset_guard", "message_watch", "skills_install"],
    }
    if not isinstance(servers, dict):
        raise ValueError("mcp_servers 配置格式错误，脚本不会修改原文件。")
    if "goofish" in servers:
        server = servers["goofish"]
        if (
            isinstance(server, dict)
            and all(server.get(key) == value for key, value in expected.items())
            and server.get("enabled", True) is True
            and "enabled_tools" not in server
        ):
            return "already-configured"
        raise ValueError("已有不同、禁用或限制工具的 goofish MCP 配置。请先在 Codex 设置中核对连接及权限，脚本不会覆盖它。")
    quote = lambda value: json.dumps(value, ensure_ascii=False)  # noqa: E731
    block = "\n".join([
        "[mcp_servers.goofish]",
        f"command = {quote(docker_command)}",
        f"args = {quote(args)}",
        "startup_timeout_sec = 30",
        "tool_timeout_sec = 180",
        "default_tools_approval_mode = \"prompt\"",
        'disabled_tools = ["auth_login", "auth_reset_guard", "message_watch", "skills_install"]',
        "",
    ])
    new_text = original + ("\n" if original and not original.endswith("\n") else "") + "\n" + block
    parse_toml(new_text)
    config_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if config_path.exists():
        fd, backup = tempfile.mkstemp(prefix=config_path.name + ".backup-", dir=config_path.parent)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(original)
    fd, temporary = tempfile.mkstemp(prefix=".goofish-config-", dir=config_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(new_text)
        os.replace(temporary, config_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return "added"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    default_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    parser.add_argument("--config", type=Path, default=default_home / "config.toml")
    args = parser.parse_args()
    docker = shutil.which("docker")
    if not docker:
        parser.exit(1, "未找到 docker，请安装并启动 Docker Desktop。\n")
    try:
        result = configure(args.config.expanduser(), docker)
    except (ValueError, OSError, ImportError) as error:
        parser.exit(1, f"MCP 配置未写入：{error}\n")
    print("闲鱼 MCP 已配置。" if result == "added" else "闲鱼 MCP 已配置，无需重复修改。")
    print("请重启 Codex，或按客户端提示重新加载 MCP 服务。")


if __name__ == "__main__":
    main()
