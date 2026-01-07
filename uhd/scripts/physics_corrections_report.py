#!/usr/bin/env python3
"""
Physics Corrections report v1
- Reads corrections.latest.jsonl
- Writes report.latest.md (no timestamps inside MD)
- Writes receipts (latest overwrite, ledger append) with UTC timestamp
Stdlib only.
"""

import json
import os
import sys
import hashlib
import datetime as _dt
from collections import Counter
from typing import List, Dict, Any, Tuple

IN_JSONL = "uhd/receipts/physics_corrections/corrections.latest.jsonl"
OUT_MD = "uhd/receipts/physics_corrections/report.latest.md"
REC_LATEST = "uhd/receipts/physics_corrections/report.receipts.latest.txt"
REC_LEDGER = "uhd/receipts/physics_corrections/report.ledger.txt"


def utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def short_text(s: str, n: int = 120) -> str:
    s = (s or "").strip().replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def load_claims(path: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            out.append(obj)
    return out


def write_md(path: str, claims: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    total = len(claims)
    tagged = sum(1 for c in claims if isinstance(c.get("model_tags"), list) and c.get("model_tags"))
    noise = sum(1 for c in claims if c.get("is_layout_noise") is True)
    tag_counter: Counter = Counter()
    layout_counter: Counter = Counter()
    rulehit_counter: Counter = Counter()
    rewrite_counter: Counter = Counter()
    for c in claims:
        tags = c.get("model_tags") or []
        if isinstance(tags, list):
            tag_counter.update(str(t) for t in tags)
        if c.get("is_layout_noise") is True:
            lts = c.get("layout_tags") or []
            if isinstance(lts, list):
                layout_counter.update(str(t) for t in lts)
        rhs = c.get("rule_hits") or []
        if isinstance(rhs, list):
            for h in rhs:
                if isinstance(h, dict):
                    key = f"{(h.get('ruleset_id') or 'NA')}:{(h.get('rule_id') or 'NA')}"
                    rulehit_counter.update([key])
        recs = c.get("recommended_rewrites") or []
        if isinstance(recs, list):
            rewrite_counter.update(str(r) for r in recs)

    def _top(counter: Counter) -> List[Tuple[str, int]]:
        items = list(counter.items())
        items.sort(key=lambda kv: (-kv[1], kv[0]))
        return items[:20]

    top_tags = _top(tag_counter)
    top_layout = _top(layout_counter)
    top_rulehits = _top(rulehit_counter)
    top_rewrites = _top(rewrite_counter)

    with open(path, "w", encoding="utf-8") as f:
        f.write("# Physics Corrections Report\n\n")
        f.write("## Summary counts\n")
        f.write(f"- Total claims: {total}\n")
        f.write(f"- Tagged claims: {tagged}\n")
        f.write("- Noise (layout) lines: %d\n" % noise)
        f.write("- Top 20 tags:\n")
        for tag, cnt in top_tags:
            f.write(f"  - {tag}: {cnt}\n")
        f.write("\n## Top layout tags\n")
        for tag, cnt in top_layout:
            f.write(f"- {tag}: {cnt}\n")
        f.write("\n## Top rule hits\n")
        for key, cnt in top_rulehits:
            f.write(f"- {key}: {cnt}\n")
        f.write("\n## Top recommended rewrites\n")
        for rw, cnt in top_rewrites:
            disp = rw if len(rw) <= 120 else rw[:119] + '…'
            f.write(f"- {disp}: {cnt}\n")
        f.write("\n## Top 50 entries\n")
        ordered = (
            [c for c in claims if (isinstance(c.get('model_tags'), list) and c.get('model_tags') and not c.get('is_layout_noise'))]
            + [c for c in claims if c.get('is_layout_noise') is True]
            + [c for c in claims if not (isinstance(c.get('model_tags'), list) and c.get('model_tags')) and not c.get('is_layout_noise')]
        )
        for c in ordered[:50]:
            rid = c.get("id")
            kind = c.get("kind")
            text = c.get("text") or c.get("normalized_text") or ""
            tags = c.get("model_tags") or []
            rh = c.get("rule_hits") or []
            recs = c.get("recommended_rewrites") or []
            rh_pairs = [
                f"{(h.get('ruleset_id') or 'NA')}:{(h.get('rule_id') or 'NA')}" for h in rh if isinstance(h, dict)
            ]
            f.write(f"- id: {rid} | kind: {kind} | text: {short_text(text)}\n")
            f.write(f"  - tags: {', '.join(tags)}\n")
            f.write(f"  - rule_hits: {', '.join(rh_pairs)}\n")
            if isinstance(recs, list) and recs:
                joined = ' | '.join(str(x) for x in recs)
                short = joined if len(joined) <= 200 else joined[:199] + '…'
                f.write(f"  - recommended_rewrite: {short}\n")


def write_receipts(inp: str, out_md: str) -> None:
    ts = utc_now_iso()
    lines = [
        f"{sha256_file(inp)}  {inp}  {ts}",
        f"{sha256_file(out_md)}  {out_md}  {ts}",
    ]
    os.makedirs(os.path.dirname(REC_LATEST), exist_ok=True)
    with open(REC_LATEST, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")
    with open(REC_LEDGER, "a", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")


def main() -> int:
    if not os.path.exists(IN_JSONL):
        print(f"Input not found: {IN_JSONL}", file=sys.stderr)
        return 2
    claims = load_claims(IN_JSONL)
    write_md(OUT_MD, claims)
    write_receipts(IN_JSONL, OUT_MD)
    print(f"Report: {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
