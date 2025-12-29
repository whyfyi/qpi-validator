#!/usr/bin/env bash
set -euo pipefail

# Run from repo root no matter where user calls it
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

tmp="$(mktemp)"
find uhd/receipts -maxdepth 1 -type f \( -name "*.json" -o -name "*.sha256" \) \
  ! -name "checksums.txt" -print0 \
  | sort -z \
  | xargs -0 sha256sum > "$tmp"

mv "$tmp" uhd/receipts/checksums.txt
echo "WROTE: $REPO_ROOT/uhd/receipts/checksums.txt"
