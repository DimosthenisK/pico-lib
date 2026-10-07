# Shared helpers for the Pico scripts. Sourced, not executed.

COMMON=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REPO=$(cd "$COMMON/.." && pwd)
export PYTHONUNBUFFERED=1
MPREMOTE="$COMMON/.venv/bin/mpremote"
DISTRO=${WSL_DISTRO_NAME:-Ubuntu-20.04}
USBIPD="/mnt/c/Program Files/usbipd-win/usbipd.exe"

if [[ ! -x "$MPREMOTE" ]]; then
  echo "Missing $MPREMOTE. Create the venv and install common/requirements.txt first." >&2
  exit 1
fi

_as_root() {
  wsl.exe -d "$DISTRO" -u root "$@"
}

locate_port() {
  local line
  line=$("$MPREMOTE" devs | awk '/2e8a:0005/ { print $1; exit }')
  if [[ -z "$line" ]] && lsusb | grep -q '2e8a:0005'; then
    _as_root modprobe cdc-acm
    line=$("$MPREMOTE" devs | awk '/2e8a:0005/ { print $1; exit }')
  fi
  if [[ -z "$line" ]]; then
    PORT=""
    return 1
  fi
  PORT=$line
}

# A hard reset unplugs the Pico from WSL. usbipd leaves it Shared on Windows.
attach_pico() {
  local line busid
  if [[ ! -x "$USBIPD" ]]; then
    echo "usbipd is not installed at $USBIPD" >&2
    return 1
  fi
  line=$("$USBIPD" list | awk '/2e8a:0005/ { print; exit }')
  if [[ -z "$line" ]]; then
    return 1
  fi
  if [[ "$line" == *"Attached"* ]]; then
    return 0
  fi
  busid=${line%% *}
  if [[ ! "$busid" =~ ^[0-9]+-[0-9]+$ ]]; then
    echo "Unexpected usbipd bus id: $busid" >&2
    return 1
  fi
  if [[ "$line" == *"Not shared"* ]]; then
    echo "Sharing Pico bus $busid (administrator approval required)"
    powershell.exe -NoProfile -Command "\$p = Start-Process -FilePath 'C:\Program Files\usbipd-win\usbipd.exe' -ArgumentList 'bind','--busid','$busid' -Verb RunAs -Wait -PassThru; if (\$p.ExitCode -ne 0) { exit \$p.ExitCode }"
  fi
  "$USBIPD" attach --wsl --busid "$busid"
}

ensure_access() {
  if [[ -w "$PORT" ]]; then
    return 0
  fi
  _as_root chgrp dialout "$PORT"
  _as_root chmod 660 "$PORT"
  if [[ ! -w "$PORT" ]]; then
    echo "Cannot write $PORT (mode $(stat -c '%A %U:%G' "$PORT"))." >&2
    exit 1
  fi
}

prepare_port() {
  if ! locate_port; then
    attach_pico || true
    locate_port || {
      echo "No MicroPython board (USB 2e8a:0005) is visible in this WSL distro." >&2
      exit 1
    }
  fi
  ensure_access
}
