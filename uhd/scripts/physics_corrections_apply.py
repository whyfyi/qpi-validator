#!/usr/bin/env python3
"""
Physics Corrections Apply v1 (deterministic scaffold -> actionable)
- Reads:  uhd/receipts/physics_claims/claims.latest.jsonl
- Loads tracked rule specs:
    - uhd/spec/physics_corrections/CCR_Core_Axioms_v1.json
    - uhd/spec/physics_corrections/QPhiD_Rules_v1.json
    - uhd/spec/physics_corrections/QGC_Rules_v1.json
    - uhd/spec/physics_corrections/AngleClock_Model_v1.json
- Writes (local-only, ignored by git):
    - uhd/receipts/physics_corrections/corrections.latest.jsonl
    - uhd/receipts/physics_corrections/corrections.ledger.txt  (sha256 receipts)
Stdlib only. No network.
"""

import datetime as _dt
import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Tuple

CLAIMS_IN = "uhd/receipts/physics_claims/claims.latest.jsonl"
OUT_JSONL = "uhd/receipts/physics_corrections/corrections.latest.jsonl"
LEDGER = "uhd/receipts/physics_corrections/corrections.ledger.txt"

RULE_FILES = [
    "uhd/spec/physics_corrections/CCR_Core_Axioms_v1.json",
    "uhd/spec/physics_corrections/QPhiD_Rules_v1.json",
    "uhd/spec/physics_corrections/QGC_Rules_v1.json",
    "uhd/spec/physics_corrections/AngleClock_Model_v1.json",
]

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def utc_ts() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_claim_text(obj: Any) -> str:
    # tolerant extraction across possible keys
    if isinstance(obj, str):
        return obj
    if not isinstance(obj, dict):
        return str(obj)

    for k in ["claim_text", "claim", "text", "statement", "line", "content"]:
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            return v

    # fallback: stable representation
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)

def build_ccr_matchers(ccr: Dict[str, Any]) -> List[Tuple[str, List[str]]]:
    aa = ccr.get("as_above", {})
    rules = aa.get("rules", [])
    out: List[Tuple[str, List[str]]] = []
    for r in rules:
        rid = r.get("id", "")
        match = r.get("match", {}) if isinstance(r, dict) else {}
        kws = match.get("any_keywords", [])
        if isinstance(rid, str) and rid and isinstance(kws, list):
            clean = [str(x).strip().lower() for x in kws if str(x).strip()]
            out.append((rid, clean))
    # deterministic order
    out.sort(key=lambda t: t[0])
    return out

def rule_hits_for_text(matchers: List[Tuple[str, List[str]]], text: str) -> List[str]:
    t = text.lower()
    hits: List[str] = []
    for rid, kws in matchers:
        for kw in kws:
            if kw and kw in t:
                hits.append(rid)
                break
    return hits

def ensure_dirs() -> None:
    os.makedirs(os.path.dirname(OUT_JSONL), exist_ok=True)
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)

def main() -> int:
    # Preconditions
    if not os.path.exists(CLAIMS_IN):
        raise SystemExit(f"claims.latest.jsonl not found: {CLAIMS_IN}\nRun physics_extract_text.py then physics_claims_build.py first.")

    for rf in RULE_FILES:
        if not os.path.exists(rf):
            raise SystemExit(f"Missing required rule file: {rf}")

    ccr = load_json(RULE_FILES[0])
    ccr_matchers = build_ccr_matchers(ccr)

    ensure_dirs()

    count = 0
    with open(CLAIMS_IN, "r", encoding="utf-8") as fin, open(OUT_JSONL, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            obj = json.loads(line)
            txt = extract_claim_text(obj)

            hits = rule_hits_for_text(ccr_matchers, txt)

            out = {
                "source": "halliday_cheatsheet",
                "claim": obj,
                "claim_text": txt,
                "rule_hits": hits,
                "correction_status": "scaffold_applied",
                "notes": "rule_hits are deterministic keyword matches; replace/extend rules with canonical CCR/QPhiD/QGC/AngleClock content."
            }
            fout.write(json.dumps(out, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1

    ts = utc_ts()
    inputs = [CLAIMS_IN] + RULE_FILES
    outputs = [OUT_JSONL]

    lines = []
    for p in inputs + outputs:
        lines.append(f"{sha256_file(p)}  {p}  {ts}")

    with open(LEDGER, "a", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")

    print(f"Corrections written: {OUT_JSONL} (count={count})")
    print(f"Ledger: {LEDGER}")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as e:
        msg = str(e)
        if msg:
            print(msg, file=sys.stderr)
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
