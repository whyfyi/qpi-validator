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
    is_layout_noise: bool
    layout_tags: List[str]
    extracted_symbols: List[str]
    extracted_units: List[str]
    extracted_equations: List[str]
    extracted_constants: List[str]
    extracted_moduli: List[str]
    extracted_ops: List[str]


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
        # layout/noise heuristics (deterministic, conservative)
        layout_tags: List[str] = []
        # empty normalized
        if not norm:
            layout_tags.append("layout:empty")
        # short content
        if norm and len(norm) < 5:
            layout_tags.append("layout:short")
        # mostly non-alphanumeric
        ns = ''.join(ch for ch in txt if not ch.isspace())
        if ns:
            alnum = sum(ch.isalnum() for ch in ns)
            if alnum / max(1, len(ns)) < 0.3:
                layout_tags.append("layout:nonalnum-heavy")
        # pdf glyphs / zero-width
        suspicious = ['\u200b', '\u200c', '\ufeff', '•', '·', '▪', '—', '–', '□']
        glyph_hits = sum(txt.count(x) for x in suspicious)
        if glyph_hits >= 2:
            layout_tags.append("layout:glyphs")
        is_noise = bool(layout_tags)

        # deterministic feature extraction
        # symbols: curated greek/math tokens
        SYMBOLS = [
            "λ", "ω", "θ", "Δ", "∑", "∫", "μ", "α", "β", "γ", "Ω", "η", "κ", "π", "χ", "φ", "ψ", "τ", "σ"
        ]
        sym_hits = sorted({s for s in SYMBOLS if s in txt})

        # units: conservative regex boundary matching
        def extract_units(text_raw: str) -> List[str]:
            t = text_raw
            hits = set()
            # canonical tokens: Hz, Pa (case-insensitive input -> canonical case); others lowercase
            patterns = [
                (r"(?<![A-Za-z0-9])kg(?![A-Za-z0-9])", "kg", 0),
                (r"(?<![A-Za-z0-9])mol(?![A-Za-z0-9])", "mol", 0),
                (r"(?<![A-Za-z0-9])cd(?![A-Za-z0-9])", "cd", 0),
                (r"(?<![A-Za-z0-9])rad/s(?![A-Za-z0-9])", "rad/s", re.IGNORECASE),
                (r"(?<![A-Za-z0-9])rad(?![A-Za-z0-9])", "rad", re.IGNORECASE),
                (r"(?<![A-Za-z0-9])m/s\^2(?![A-Za-z0-9])", "m/s^2", 0),
                (r"(?<![A-Za-z0-9])m/s(?![A-Za-z0-9])", "m/s", 0),
                (r"(?<![A-Za-z0-9])hz(?![A-Za-z0-9])", "Hz", re.IGNORECASE),
                (r"(?<![A-Za-z0-9])pa(?![A-Za-z0-9])", "Pa", re.IGNORECASE),
            ]
            for pat, canon, flags in patterns:
                if re.search(pat, t, flags):
                    hits.add(canon)
            return sorted(hits)

        unit_hits = extract_units(txt)

        # equations: short snippets around '=' or '≈', normalized whitespace, max ~60 chars
        eq_hits = []
        for m in re.finditer(r"[=≈]", txt):
            start = max(0, m.start() - 30)
            end = min(len(txt), m.end() + 30)
            snippet = txt[start:end]
            snippet = re.sub(r"\s+", " ", snippet.strip())
            if 1 <= len(snippet) <= 60:
                eq_hits.append(snippet)
        eq_hits = sorted(set(eq_hits))

        # constants: conservative word-boundary for latin tokens; direct symbol checks for unicode
        def extract_constants(text_raw: str) -> List[str]:
            hits = set()
            # unicode symbols direct
            for sym in ["π", "φ", "τ", "ℏ", "ħ"]:
                if sym in text_raw:
                    hits.add(sym)
            # latin tokens with word boundaries
            latin_specs = [
                (r"(?i)(?<![A-Za-z0-9_])pi(?![A-Za-z0-9_])", "pi"),
                (r"(?i)(?<![A-Za-z0-9_])phi(?![A-Za-z0-9_])", "phi"),
                (r"(?i)(?<![A-Za-z0-9_])tau(?![A-Za-z0-9_])", "tau"),
                (r"(?<![A-Za-z0-9_])e(?![A-Za-z0-9_])", "e"),
                (r"(?<![A-Za-z0-9_])c(?![A-Za-z0-9_])", "c"),
                (r"(?<![A-Za-z0-9_])G(?![A-Za-z0-9_])", "G"),
                (r"(?<![A-Za-z0-9_])h(?![A-Za-z0-9_])", "h"),
            ]
            for pat, canon in latin_specs:
                if re.search(pat, text_raw):
                    hits.add(canon)
            return sorted(hits)

        const_hits = extract_constants(txt)

        # moduli: detect canonical 'mod N'
        def extract_moduli(text_raw: str) -> List[str]:
            hits = set()
            for m in re.finditer(r"(?i)\bmod\s*(\d{1,4})\b", text_raw):
                hits.add(f"mod {m.group(1)}")
            for m in re.finditer(r"≡\s*\(\s*mod\s*(\d{1,4})\s*\)", text_raw):
                hits.add(f"mod {m.group(1)}")
            # percent-operator style modulo (conservative: percent as its own token)
            for m in re.finditer(r"(?<!\S)%\s*(\d{1,4})\b", text_raw):
                hits.add(f"mod {m.group(1)}")
            return sorted(hits)

        mod_hits = extract_moduli(txt)

        # ops: calculus/geometry operators (canonical tokens)
        def extract_ops(text_raw: str) -> List[str]:
            ops = set()
            if "∫" in text_raw:
                ops.add("integral")
            if "∑" in text_raw:
                ops.add("sum")
            if "Δ" in text_raw:
                ops.add("delta")
            if "∂" in text_raw:
                ops.add("partial")
            if "∇" in text_raw:
                ops.add("nabla")
            if re.search(r"d\s*/\s*d\s*[a-zA-Z]", text_raw):
                ops.add("derivative")
            return sorted(ops)

        op_hits = extract_ops(txt)
        yield Claim(
            id=cid,
            kind=kind,
            text=txt,
            normalized_text=norm,
            source_span=(i, i),
            is_layout_noise=is_noise,
            layout_tags=sorted(set(layout_tags)),
            extracted_symbols=sym_hits,
            extracted_units=unit_hits,
            extracted_equations=eq_hits,
            extracted_constants=const_hits,
            extracted_moduli=mod_hits,
            extracted_ops=op_hits,
        )


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
                "is_layout_noise": c.is_layout_noise,
                "layout_tags": c.layout_tags,
                "extracted_symbols": c.extracted_symbols,
                "extracted_units": c.extracted_units,
                "extracted_equations": c.extracted_equations,
                "extracted_constants": c.extracted_constants,
                "extracted_moduli": c.extracted_moduli,
                "extracted_ops": c.extracted_ops,
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
