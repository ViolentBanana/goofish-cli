#!/bin/bash
set -euo pipefail
task_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$task_root"
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
task_skip_login=0
case "${1:-}" in
    '') ;;
    --skip-login) task_skip_login=1 ;;
    --help|-h) echo '用法：bash scripts/setup-docker-codex.sh [--skip-login]'; exit 0 ;;
    *) echo '未知参数；使用 --help 查看用法。' >&2; exit 2 ;;
esac
if [ "$#" -gt 1 ]; then
    echo '只支持 --skip-login 一个可选参数。' >&2
    exit 2
fi
command -v docker >/dev/null 2>&1 || { echo '请先安装 Docker Desktop（或 Docker Engine + Compose）。' >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo 'Docker 尚未启动，请启动 Docker Desktop 后重试。' >&2; exit 1; }
docker compose version >/dev/null
if [ "$task_skip_login" -eq 0 ] && [ "$(uname -s)" != Darwin ]; then
    echo '自动读取 Chrome 登录态支持 macOS。Linux 请加 --skip-login，随后按 DOCKER.md 导入 Cookie JSON。' >&2
    exit 1
fi
task_python="$(bash scripts/prepare-host-python.sh)"
echo '正在构建并启动闲鱼容器；首次需要下载 Linux Chrome……'
docker compose up -d --build --wait --wait-timeout 180
docker exec goofish-cli python /usr/local/lib/goofish/verify_runtime.py
"$task_python" scripts/configure_codex_mcp.py
if [ "$task_skip_login" -eq 0 ]; then
    "$task_python" docker/import_chrome_cookies.py
    docker exec goofish-cli python /usr/local/lib/goofish/verify_runtime.py --require-login
else
    echo '已跳过账号登录。实际调用闲鱼前，请先按 DOCKER.md 导入你的登录态。'
fi
echo '部署及 Codex MCP 配置完成。重启 Codex，然后使用 README 中的提示词。'
