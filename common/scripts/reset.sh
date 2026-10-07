#!/usr/bin/env bash
# Hard-reset the Pico (machine.reset()) and wait until its serial port is back.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

prepare_port
echo "Hard reset on $PORT"
"$MPREMOTE" connect "$PORT" reset

PORT=""
for _ in $(seq 1 40); do
  attach_pico || true
  if locate_port; then
    break
  fi
  sleep 0.25
done

if [[ -z "$PORT" ]]; then
  echo "Reset was sent, but 2e8a:0005 did not come back into WSL." >&2
  exit 1
fi

ensure_access
echo "Board is back on $PORT"
"$MPREMOTE" devs | awk '/2e8a:0005/'
