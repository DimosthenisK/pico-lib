#!/usr/bin/env bash
# Create lib/<name> with an empty package and a mip package.json.
set -euo pipefail

REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
name=${1:-}

if [[ ! "$name" =~ ^[a-z][a-z0-9_]*$ ]]; then
  echo "Usage: ./common/scripts/new-module.sh <name>" >&2
  echo "Name must be a lowercase Python identifier, for example sensor." >&2
  exit 1
fi

dest="$REPO/lib/$name"
if [[ -e "$dest" ]]; then
  echo "$name already exists at lib/$name" >&2
  exit 1
fi

mkdir -p "$dest"
printf '"""%s"""\n' "$name" > "$dest/__init__.py"
python3 - "$dest/package.json" "$name" << 'PY'
import json
import sys

path, name = sys.argv[1], sys.argv[2]
with open(path, "w") as handle:
    json.dump(
        {
            "urls": [[name + "/__init__.py", "__init__.py"]],
            "version": "0.1.0",
        },
        handle,
        indent=2,
    )
    handle.write("\n")
PY

echo "Created lib/$name at version 0.1.0"
