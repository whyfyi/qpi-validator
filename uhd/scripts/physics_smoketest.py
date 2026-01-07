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
FIXTURE_EXT = "uhd/fixtures/physics_claims_ccr_qgc_qphid_synthetic.jsonl"
APPLY = ["python3", "uhd/scripts/physics_corrections_apply.py"]
OUT = "uhd/receipts/physics_corrections/corrections.latest.jsonl"
REPORT = ["python3", "uhd/scripts/physics_corrections_report.py"]
REPORT_MD = "uhd/receipts/physics_corrections/report.latest.md"


def run_apply(claims_path: str) -> None:
    cmd = APPLY + ["--claims", claims_path]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)
        raise SystemExit(f"apply failed: {r.returncode}")

def run_report() -> None:
    r = subprocess.run(REPORT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr, file=sys.stderr)
        raise SystemExit(f"report failed: {r.returncode}")


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
            # Feature extraction lists must exist
            for k in ("extracted_symbols", "extracted_units", "extracted_equations"):
                v = obj.get(k)
                if not isinstance(v, list):
                    raise SystemExit(f"line {i}: {k} not list")
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
    # Precision checks: ensure certain noisy lines do not over-tag
    def read_out() -> list:
        with open(OUT, "r", encoding="utf-8") as f:
            return [json.loads(ln) for ln in f if ln.strip()]
    objs = read_out()
    precA = next((o for o in objs if o.get("id") == "n16"), None)
    precB = next((o for o in objs if o.get("id") == "n17"), None)
    if not precA or not precB:
        raise SystemExit("precision asserts: fixture lines n16/n17 not found")
    if "QGG:curvature" in set(precA.get("model_tags") or []):
        raise SystemExit("precision A incorrectly tagged QGG:curvature for 'kg' line")
    tagsB = set(precB.get("model_tags") or [])
    if "QGL:wave" in tagsB or "QGL:standing_wave" in tagsB:
        raise SystemExit("precision B incorrectly tagged QGL:wave for simple equation")
    # Report exists and sections present, and no timestamps inside MD
    run_report()
    if not os.path.exists(REPORT_MD):
        raise SystemExit("report.latest.md not found")
    with open(REPORT_MD, "r", encoding="utf-8") as f:
        md = f.read()
    required = [
        "## Top layout tags",
        "## Top rule hits",
        "## Top recommended rewrites",
        "## Top 50 entries",
    ]
    for h in required:
        if h not in md:
            raise SystemExit(f"missing section in report: {h}")
    if ("T" in md and "Z" in md) or "+00:00" in md:
        raise SystemExit("report appears to contain timestamps")
    # Extended fixture checks: determinism and ruleset coverage
    first_ext = run_once(FIXTURE_EXT)
    second_ext = run_once(FIXTURE_EXT)
    if first_ext != second_ext:
        raise SystemExit("outputs differ between runs (extended)")
    # Parse and assert coverage
    with open(OUT, "r", encoding="utf-8") as f:
        objs_ext = [json.loads(ln) for ln in f if ln.strip()]
    def has_ruleset(rsid: str) -> bool:
        return any(any(h.get("ruleset_id") == rsid for h in o.get("rule_hits") or []) for o in objs_ext)
    if not has_ruleset("CCR_CORE_AXIOMS_V1") and not has_ruleset("CCR.v1"):
        # Allow either id, depending on CCR rules structure
        raise SystemExit("expected at least one CCR ruleset hit in extended fixture")
    if not has_ruleset("QGC.v1"):
        raise SystemExit("expected at least one QGC ruleset hit in extended fixture")
    if not has_ruleset("QPhiD.v1"):
        raise SystemExit("expected at least one QPhiD ruleset hit in extended fixture")
    if not has_ruleset("AngleClock.v1"):
        raise SystemExit("expected at least one AngleClock.v1 ruleset hit in extended fixture")
    # Additional precision checks on extended fixture reusable negatives
    neg_a = next((o for o in objs_ext if o.get("id") == "c21"), None)  # mass 5 kg
    neg_b = next((o for o in objs_ext if o.get("id") == "c22"), None)  # x = v t
    if neg_a and ("QGG:curvature" in set(neg_a.get("model_tags") or []) or "QGC:curvature" in set(neg_a.get("model_tags") or [])):
        raise SystemExit("extended precision: 'kg' line incorrectly tagged curvature")
    if neg_b and ("QGL:wave" in set(neg_b.get("model_tags") or []) or "QGL:standing_wave" in set(neg_b.get("model_tags") or [])):
        raise SystemExit("extended precision: simple equation incorrectly tagged wave")
    # AngleClock precision negatives
    neg_c = next((o for o in objs_ext if o.get("id") == "c43"), None)
    neg_d = next((o for o in objs_ext if o.get("id") == "c44"), None)
    neg_e = next((o for o in objs_ext if o.get("id") == "c45"), None)
    def has_ac_tag(o) -> bool:
        return any(str(t).startswith("AngleClock:") for t in (o.get("model_tags") or []))
    for nid, obj in [("c43", neg_c), ("c44", neg_d), ("c45", neg_e)]:
        if obj and has_ac_tag(obj):
            raise SystemExit(f"AngleClock precision: {nid} incorrectly tagged AngleClock:*")
    print("SMOKETEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
