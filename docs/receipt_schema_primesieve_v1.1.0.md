Receipt Schema: primesieve v1.1.0

This document specifies a stable, verifiable JSON receipt schema for counting twin primes with `primesieve`.

Top-level structure

- receipt_metadata
- environment
- execution
- results
- integrity

Fields

- receipt_metadata
  - schema_version: Receipt schema version string. Example: "1.1.0".
  - generated_utc: ISO-8601 UTC timestamp of receipt creation.
  - repository: Repository identifier or URL where the receipt was produced.
  - commit_hash: Git commit hash for the repository at receipt time.
  - workflow: CI workflow name (e.g., GitHub Actions), or "local" when run outside CI.
  - run_id: CI run identifier, or "local" when run outside CI.
  - actor: CI actor/user, or "local" when run outside CI.

- environment
  - os: Operating system (e.g., "Linux", "Darwin", "Windows").
  - kernel: Kernel or OS release (e.g., "5.15.0-...", "22.6.0").
  - arch: Machine architecture (e.g., "x86_64", "arm64").
  - cpu_model: Best-effort CPU model string.
  - python_version: Python version string (e.g., from `sys.version`).
  - primesieve_version: Version string from `primesieve --version`.

- execution
  - tool: Name of tool used ("primesieve").
  - mode: Mode used for counting twin primes ("-c2").
  - command: Exact command invoked.
  - args
    - n: Upper bound N (integer).
  - wall_time_seconds: Elapsed wall time to execute the command (float seconds).

- results
  - n: Upper bound N (integer), duplicated for clarity and filtering.
  - twin_prime_count: Number of twin prime pairs up to N (integer).
  - unit: Unit for the count ("pairs").

- integrity
  - method: Integrity method string ("sha256").
  - digest: Hex-encoded SHA-256 digest of the canonical payload described below.

Integrity: canonical payload

- The integrity digest is computed over the JSON object with the top-level field `integrity` removed.
- Canonical JSON serialization must use UTF-8 bytes with the following encoder settings:
  - Keys sorted (`sort_keys=True`).
  - Minimal separators (`separators=(",", ":")`).
- The resulting bytes are hashed with SHA-256; the hex digest is stored in `integrity.digest`.

Notes

- A separate companion file `results/primesieve_twin_count_<N>.sha256` contains the SHA-256 of the full JSON file on disk. This is used by repository-wide integrity checks and CI.
- Historical receipts (pre-1.1.0) remain unchanged.

