#!/bin/bash
# Print only the Python executable on stdout so callers can capture it safely.
set -euo pipefail
task_root="$(cd "$(dirname "$0")/.." && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
    echo '需要 Python 3.9 或更高版本，请先安装 Python 3。' >&2
    exit 1
fi
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' || {
    echo '需要 Python 3.9 或更高版本。' >&2
    exit 1
}
task_venv="$task_root/.cookie-import-venv"
if [ ! -x "$task_venv/bin/python" ]; then
    echo '首次运行：正在准备主机工具环境……' >&2
    python3 -m venv "$task_venv"
fi
if ! "$task_venv/bin/python" -c 'import browser_cookie3, tomli' >/dev/null 2>&1; then
    "$task_venv/bin/python" -m pip install --disable-pip-version-check -r "$task_root/docker/host-requirements.txt" >&2
fi
printf '%s\n' "$task_venv/bin/python"
