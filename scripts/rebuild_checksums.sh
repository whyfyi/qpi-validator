#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Canonical SHA-256 checksums for receipts in results/
{
  echo "# Canonical SHA-256 checksums for receipts in results/"
  echo "# Recompute with: sha256sum results/*.json"
  echo "# Generated UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > results/checksums.txt

# Stable ordering
for f in $(ls -1 results/*.json | sort); do
  sha256sum "$f" >> results/checksums.txt
done

echo "REBUILT: results/checksums.txt"
tail -n 20 results/checksums.txt
