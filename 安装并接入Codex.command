#!/bin/bash
cd "$(dirname "$0")" || exit 1
bash scripts/setup-docker-codex.sh "$@"
task_result=$?
echo
if [ -t 0 ]; then
    read -r -p '按回车键关闭窗口……' task_reply
fi
exit "$task_result"
