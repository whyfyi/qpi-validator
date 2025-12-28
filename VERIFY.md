How to Verify Receipts (No Build Needed)

This guide shows how anyone can independently verify the integrity of published receipts and re-run the checksum process locally.

Prerequisites

- Linux/macOS with `sha256sum` (or `shasum -a 256` as an alternative)
- Bash shell

Steps

- Verify checksums for tracked receipts
  - Run: `sha256sum -c results/checksums.txt`
  - Expected: All lines report "OK".

- Ensure every `results/*.json` is listed
  - Run: `for f in $(ls -1 results/*.json | sort); do grep -Fq " $f" results/checksums.txt || echo "MISSING: $f"; done`
  - Expected: No output. Missing entries should be added via `scripts/rebuild_checksums.sh`.

- Rebuild checksums after adding or updating receipts
  - Run: `bash scripts/rebuild_checksums.sh`
  - Inspect: `tail -n 10 results/checksums.txt`

- Verify a single receipt file
  - Compute sha256: `sha256sum results/primesieve_twin_count_<N>.json`
  - Compare with the companion file: `cat results/primesieve_twin_count_<N>.sha256`

- Inspect embedded integrity in schema v1.1.0 receipts
  - The JSON contains an `integrity` object with fields `method` ("sha256") and `digest`.
  - To recompute:
    - Parse JSON, remove the `integrity` field, re-serialize canonically (sorted keys, separators `,` and `:`), hash with SHA-256.
    - Compare the hex digest with `integrity.digest`.

Notes

- Historical receipts (pre-1.1.0) do not contain embedded integrity; use the file-level `.sha256` and `results/checksums.txt` for those.
- CI (`.github/workflows/integrity.yml`) enforces checksum correctness and coverage for all `results/*.json` files.

