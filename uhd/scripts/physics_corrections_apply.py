#!/usr/bin/env python3
"""
Physics Corrections v1 — scaffold apply
- Verifies presence of tracked rule files
- Requires local claims.latest.jsonl; if missing, exits with guidance
- Pass-through: copies claims to corrections.latest.jsonl with added fields
- Writes receipts (overwrite ledger) with sha256 of inputs+rules+output
Stdlib only. No network.
"""

import hashlib
import json
import os
import sys
import datetime as _dt
from typing import List

SPEC_PATH = "uhd/spec/physics_corrections/Physics_Corrections_Spec_v1.json"
CLAIMS_PATH = "uhd/receipts/physics_claims/claims.latest.jsonl"
RULES = [
    "uhd/spec/physics_corrections/CCR_Core_Axioms_v1.json",
    "uhd/spec/physics_corrections/QPhiD_Rules_v1.json",
    "uhd/spec/physics_corrections/QGC_Rules_v1.json",
    "uhd/spec/physics_corrections/AngleClock_Model_v1.json",
]
OUT_JSONL = "uhd/receipts/physics_corrections/corrections.latest.jsonl"
LEDGER = "uhd/receipts/physics_corrections/corrections.ledger.txt"


def utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_rules_exist(paths: List[str]) -> None:
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        print("Missing required rule spec file(s):", file=sys.stderr)
        for p in missing:
            print(f" - {p}", file=sys.stderr)
        sys.exit(2)


def ensure_claims_exists(path: str) -> None:
    if not os.path.exists(path):
        print(
            "Claims file not found. Run prior stages:\n"
            "  1) python3 uhd/scripts/physics_extract_text.py --pdf uhd/imports/physics/Halliday_Cheatsheet.pdf\n"
            "  2) python3 uhd/scripts/physics_claims_build.py\n",
            file=sys.stderr,
        )
        sys.exit(2)


def apply_pass_through(claims_path: str, out_path: str) -> int:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    count = 0
    with open(claims_path, "r", encoding="utf-8", errors="replace") as fin, \
         open(out_path, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                # Skip malformed lines in scaffold
                continue
            obj["correction_status"] = "unprocessed"
            obj["notes"] = "scaffold"
            fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
            count += 1
    return count


def write_ledger(paths: List[str]) -> None:
    ts = utc_now_iso()
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8") as f:
        for p in paths:
            f.write(f"{sha256_file(p)}  {p}  {ts}\n")


def main() -> int:
    # Load spec minimally to assert structure exists (optional for scaffold)
    if not os.path.exists(SPEC_PATH):
        print(f"Spec not found: {SPEC_PATH}", file=sys.stderr)
        return 2

    require_rules_exist(RULES)
    ensure_claims_exists(CLAIMS_PATH)

    written = apply_pass_through(CLAIMS_PATH, OUT_JSONL)

    # Inputs for ledger: claims + rules + output
    ledger_paths = [CLAIMS_PATH, *RULES, OUT_JSONL]
    write_ledger(ledger_paths)

    print(f"Corrections written: {OUT_JSONL} (count={written})\nLedger: {LEDGER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
