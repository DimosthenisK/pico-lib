#!/usr/bin/env bash
# Copy lib packages and common/sample onto the Pico, run the sample entry,
# and stay on the serial port until that program finishes.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

entry=${1:-sample/blink.py}
if [[ "$entry" == /* || "$entry" == *..* || "$entry" != sample/* ]]; then
  echo "Entry point must be a path under common/sample, for example sample/blink.py" >&2
  exit 1
fi
if [[ ! -f "$COMMON/$entry" ]]; then
  echo "Missing $COMMON/$entry" >&2
  exit 1
fi

declare -a local_files=()
declare -a remote_files=()
declare -A seen_dirs=()
declare -a dirs=()

add_file() {
  local src=$1 remote=$2 dir
  local_files+=("$src")
  remote_files+=("$remote")
  dir=$(dirname "$remote")
  while [[ "$dir" != "." ]]; do
    if [[ -z "${seen_dirs[$dir]+x}" ]]; then
      seen_dirs[$dir]=1
      dirs+=("$dir")
    fi
    dir=$(dirname "$dir")
  done
}

collect_tree() {
  local root=$1 remote_root=$2
  while IFS= read -r -d '' file; do
    local rel=${file#"$root"/}
    add_file "$file" "$remote_root/$rel"
  done < <(find -P "$root" -name '__pycache__' -prune -o -type f ! -name '.*' -print0)
}

if [[ -d "$REPO/lib" ]]; then
  for pkg in "$REPO/lib"/*; do
    [[ -d "$pkg" && ! -L "$pkg" ]] || continue
    collect_tree "$pkg" "$(basename "$pkg")"
  done
  shopt -s nullglob
  for file in "$REPO/lib"/*.py; do
    add_file "$file" "$(basename "$file")"
  done
  shopt -u nullglob
fi

collect_tree "$COMMON/sample" "sample"

found_entry=0
for remote in "${remote_files[@]}"; do
  if [[ "$remote" == "$entry" ]]; then
    found_entry=1
    break
  fi
done
if [[ "$found_entry" -ne 1 ]]; then
  echo "$entry is not one of the files that will be copied." >&2
  exit 1
fi

if [[ ${#dirs[@]} -gt 0 ]]; then
  mapfile -t dirs < <(printf '%s\n' "${dirs[@]}" | awk -F/ '{ print NF "\t" $0 }' | sort -n -k1,1 | cut -f2-)
fi

mkdir_src=""
if [[ ${#dirs[@]} -gt 0 ]]; then
  mkdir_src='import os
'
  for dir in "${dirs[@]}"; do
    lit=$("$COMMON/.venv/bin/python" -c 'import sys; print(repr(sys.argv[1]))' "$dir")
    mkdir_src+="try:
 os.mkdir($lit)
except OSError:
 pass
"
  done
fi

prepare_port

args=("$MPREMOTE" connect "$PORT")
if [[ -n "$mkdir_src" ]]; then
  args+=(exec "$mkdir_src" +)
fi
for i in "${!local_files[@]}"; do
  args+=(cp "${local_files[$i]}" ":${remote_files[$i]}" +)
done
args+=(run "$COMMON/$entry")

echo "Copying ${#local_files[@]} file(s) to $PORT, then running $entry"
echo "Output follows until the program finishes. Ctrl-C stops following."
"${args[@]}"
