#!/bin/bash
set -u
cd "$(dirname "$0")" || exit 1
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
run_import() {
    if [ "$(uname -s)" != Darwin ]; then
        echo '自动读取 Chrome 登录态目前支持 macOS；其他系统请按 DOCKER.md 导入 Cookie JSON。' >&2
        return 1
    fi
    echo '请先在 Mac Chrome 中登录 https://www.goofish.com'
    echo '本工具会直接把登录态导入本机 Docker，无需手动复制 Cookie。'
    local task_python
    task_python="$(bash scripts/prepare-host-python.sh)" || return 1
    "$task_python" docker/import_chrome_cookies.py "$@"
}
run_import "$@"
task_result=$?
echo
if [ -t 0 ]; then
    read -r -p '按回车键关闭窗口……' task_reply
fi
exit "$task_result"
