#!/bin/sh
# Fail if any argument file contains CR (0x0D).
# Usage: sh scripts/check_line_endings.sh [file ...]
# Default: scripts/build_shadow_spool.sh
set -eu

CR=$(printf '\015')

check_one() {
  file=$1
  if [ ! -f "$file" ]; then
    echo "missing file: $file" >&2
    exit 1
  fi
  if grep -q "$CR" "$file"; then
    echo "CRLF detected in $file" >&2
    exit 1
  fi
}

if [ $# -eq 0 ]; then
  set -- scripts/build_shadow_spool.sh
fi

for file in "$@"; do
  check_one "$file"
done

echo "line_endings=lf ok"
