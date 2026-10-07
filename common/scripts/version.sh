#!/usr/bin/env bash
# Set or bump the version in lib/<name>/package.json.
set -euo pipefail

REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
name=${1:-}
change=${2:-}

if [[ -z "$name" || -z "$change" ]]; then
  echo "Usage: ./common/scripts/version.sh <name> <version|major|minor|patch>" >&2
  exit 1
fi

manifest="$REPO/lib/$name/package.json"
if [[ ! -f "$manifest" ]]; then
  echo "No package.json at lib/$name" >&2
  exit 1
fi

python3 - "$manifest" "$change" << 'PY'
import json
import sys

path, change = sys.argv[1], sys.argv[2]
with open(path) as handle:
    document = json.load(handle)

def fail(message):
    print(message, file=sys.stderr)
    sys.exit(1)

def dotted(value):
    parts = value.split(".")
    if not parts or not all(part.isdigit() for part in parts):
        fail("Version must be numbers separated by dots, or major, minor, or patch.")
    return parts

if change in ("major", "minor", "patch"):
    parts = dotted(str(document.get("version", "")))
    if len(parts) != 3:
        fail(document.get("version", "") + " is not major.minor.patch. Set an explicit version instead.")
    major, minor, patch = (int(part) for part in parts)
    if change == "major":
        major, minor, patch = major + 1, 0, 0
    elif change == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    document["version"] = "{}.{}.{}".format(major, minor, patch)
else:
    dotted(change)
    document["version"] = change

with open(path, "w") as handle:
    json.dump(document, handle, indent=2)
    handle.write("\n")
print(document["version"])
PY
