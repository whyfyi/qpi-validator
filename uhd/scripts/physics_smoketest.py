#!/usr/bin/env python3
"""
CI smoketest for physics corrections (no PDFs, no receipts committed)
- Uses synthetic fixture to build a temp claims.latest.jsonl
- Runs physics_corrections_apply.py with --claims pointing to temp file
- Verifies output exists, each line JSON, rule_hits is list, model_tags sorted unique
- Runs twice and asserts outputs identical (byte-for-byte)
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

FIXTURE = "uhd/fixtures/physics_claims_synthetic.jsonl"
FIXTURE_NOISY = "uhd/fixtures/physics_claims_noisy_synthetic.jsonl"
APPLY = ["python3", "uhd/scripts/physics_corrections_apply.py"]
OUT = "uhd/receipts/physics_corrections/corrections.latest.jsonl"


def run_apply(claims_path: str) -> None:
    cmd = APPLY + ["--claims", claims_path]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)
        raise SystemExit(f"apply failed: {r.returncode}")


def verify_output(out_path: str) -> bytes:
    if not os.path.exists(out_path):
        raise SystemExit(f"output not found: {out_path}")
    with open(out_path, "rb") as f:
        b = f.read()
    # Per-line checks
    with open(out_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            rh = obj.get("rule_hits")
            if not isinstance(rh, list):
                raise SystemExit(f"line {i}: rule_hits not list")
            tags = obj.get("model_tags")
            if not isinstance(tags, list):
                raise SystemExit(f"line {i}: model_tags not list")
            if tags != sorted(tags) or len(tags) != len(set(tags)):
                raise SystemExit(f"line {i}: model_tags not sorted unique")
    return b


def run_once(fixture: str) -> bytes:
    import tempfile, shutil, os
    with tempfile.TemporaryDirectory() as td:
        claims = os.path.join(td, "claims.latest.jsonl")
        shutil.copyfile(fixture, claims)
        run_apply(claims)
        return verify_output(OUT)

def count_noise() -> int:
    import json
    c = 0
    with open(OUT, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get("is_layout_noise") is True:
                c += 1
    return c

def main() -> int:
    # Determinism on clean synthetic fixture
    first = run_once(FIXTURE)
    second = run_once(FIXTURE)
    if first != second:
        raise SystemExit("outputs differ between runs (synthetic)")

    # Noise assertions on noisy fixture
    run_once(FIXTURE_NOISY)
    n = count_noise()
    if n < 3:
        raise SystemExit(f"expected at least 3 noise lines, got {n}")
    print("SMOKETEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
