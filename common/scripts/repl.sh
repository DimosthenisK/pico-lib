#!/usr/bin/env bash
# Open the MicroPython REPL. Leave it with Ctrl-] or Ctrl-x.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

prepare_port
echo "REPL on $PORT"
exec "$MPREMOTE" connect "$PORT" repl
