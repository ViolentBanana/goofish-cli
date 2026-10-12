#!/bin/sh
set -eu
Xvfb "$DISPLAY" -screen 0 1440x900x24 -nolisten tcp >/tmp/goofish-xvfb.log 2>&1 &
exec "$@"
