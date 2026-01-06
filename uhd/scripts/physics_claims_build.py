#!/usr/bin/env python3
"""
Physics Claims Index builder v1
- Reads extracted text (halliday_cheatsheet.latest.txt)
- Extracts best-effort claims into JSONL
- Writes a top-100 summary extract
- Writes receipts for input + outputs (latest overwrite, ledger append)
Stdlib only. No network.
"""

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Iterable, List, Tuple

INPUT_TXT = "uhd/receipts/physics/halliday_cheatsheet.latest.txt"
OUT_JSONL = "uhd/receipts/physics_claims/claims.latest.jsonl"
OUT_EXTRACT = "uhd/receipts/physics_claims/claims.extract.latest.txt"
REC_LATEST = "uhd/receipts/physics_claims/claims.receipts.latest.txt"
REC_LEDGER = "uhd/receipts/physics_claims/claims.ledger.txt"


@dataclass
class Claim:
    id: str
    kind: str
    text: str
    normalized_text: str
    source_span: Tuple[int, int]


def utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def classify(text: str) -> str:
    t = text.strip()
    low = t.lower()
    # Heuristics
    if re.search(r"[=≈∝]", t) and re.search(r"\d", t):
        return "equation"
    if ":" in t and len(t.split(":", 1)[0]) <= 32:
        return "definition"
    if re.search(r"\b(\d+(?:\.\d+)?)\s*(m|s|kg|n|j|w|pa|hz|c|g|k|r|mol|cd)(\b|/|\^)", low):
        return "unit"
    if re.search(r"\b(c|g|h|k|e|r|pi|π)\b", low) and "=" in t:
        return "constant"
    if low.startswith(('-', '*', 'note', 'remember')):
        return "note"
    return "other"


def iter_claims(lines: Iterable[str], max_lines: int) -> Iterable[Claim]:
    for i, line in enumerate(lines, start=1):
        if i > max_lines:
            break
        txt = line.rstrip("\n")
        if not txt.strip():
            continue
        norm = normalize(txt)
        cid = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        kind = classify(txt)
        yield Claim(id=cid, kind=kind, text=txt, normalized_text=norm, source_span=(i, i))


def write_jsonl(path: str, claims: Iterable[Claim]) -> int:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    count = 0
    with open(path, "w", encoding="utf-8") as f:
        for c in claims:
            obj = {
                "id": c.id,
                "kind": c.kind,
                "text": c.text,
                "normalized_text": c.normalized_text,
                "source_span": list(c.source_span),
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            count += 1
    return count


def write_extract(path: str, claims_path: str, sample: List[Claim]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("Physics Claims v1 — Top 100\n")
        f.write(f"Source claims: {claims_path}\n\n")
        for c in sample[:100]:
            f.write(f"L{c.source_span[0]} [{c.kind}] {c.text}\n")


def write_receipts(latest_path: str, ledger_path: str, lines: List[str]) -> None:
    os.makedirs(os.path.dirname(latest_path), exist_ok=True)
    with open(latest_path, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    with open(ledger_path, "a", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln + "\n")


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description="Build Physics Claims Index v1")
    p.add_argument("--input", default=INPUT_TXT, help="Path to halliday_cheatsheet.latest.txt")
    p.add_argument("--max-lines", type=int, default=200000, help="Max lines to read from input")
    args = p.parse_args(argv)

    if not os.path.exists(args.input):
        print(f"Input text not found: {args.input}", file=sys.stderr)
        return 2

    with open(args.input, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    claims_list = list(iter_claims(lines, args.max_lines))
    written = write_jsonl(OUT_JSONL, iter(claims_list))
    write_extract(OUT_EXTRACT, OUT_JSONL, claims_list)

    ts = utc_now_iso()
    h_in = sha256_file(args.input)
    h_jsonl = sha256_file(OUT_JSONL)
    h_extract = sha256_file(OUT_EXTRACT)
    rec_lines = [
        f"{h_in}  {args.input}  {ts}",
        f"{h_jsonl}  {OUT_JSONL}  {ts}",
        f"{h_extract}  {OUT_EXTRACT}  {ts}",
    ]
    write_receipts(REC_LATEST, REC_LEDGER, rec_lines)

    print(f"Claims written: {OUT_JSONL} (count={written})\nExtract summary: {OUT_EXTRACT}\nReceipts: {REC_LATEST} and appended -> {REC_LEDGER}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
