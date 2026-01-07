#!/usr/bin/env python3
"""
Physics Corrections v1 — scaffold apply with rules
- Verifies presence of tracked rule files
- Requires local claims.latest.jsonl; if missing, exits with guidance
- Applies rulesets (substring, case-insensitive) deterministically
- Pass-through fields preserved; adds rule_hits and model_tags
- Writes receipts (overwrite ledger) with sha256 of inputs+rules+output
Stdlib only. No network.
"""

import hashlib
import json
import os
import sys
import datetime as _dt
import argparse
import re
from typing import List, Dict, Any

SPEC_PATH = "uhd/spec/physics_corrections/Physics_Corrections_Spec_v1.json"
CLAIMS_PATH = "uhd/receipts/physics_claims/claims.latest.jsonl"
RULE_ORDER = [
    ("uhd/spec/physics_corrections/CCR_Core_Axioms_v1.json", "CCR.v1"),
    ("uhd/spec/physics_corrections/QPhiD_Rules_v1.json", "QPhiD.v1"),
    ("uhd/spec/physics_corrections/QGC_Rules_v1.json", "QGC.v1"),
    # AngleClock: switch from model placeholder to first-class ruleset
    ("uhd/spec/physics_corrections/AngleClock_Rules_v1.json", "AngleClock.v1"),
    ("uhd/spec/physics_corrections/QGG_Rules_v1.json", "QGG.v1"),
    ("uhd/spec/physics_corrections/QGL_Rules_v1.json", "QGL.v1"),
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
        msg = (
            "Claims file not found. Run prior stages:\n"
            "  1) python3 uhd/scripts/physics_extract_text.py --pdf uhd/imports/physics/Halliday_Cheatsheet.pdf\n"
            "  2) python3 uhd/scripts/physics_claims_build.py\n"
        )
        print(msg, file=sys.stderr)
        sys.exit(2)


def load_ruleset(path: str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        rs = json.load(f)
    aa = rs.get('as_above', {})
    rules = aa.get('rules', [])
    # Normalize rule match to list[str]
    for r in rules:
        m = r.get('match', [])
        if isinstance(m, dict):
            # normalize match object lists to list[str]
            for k in ('any_substrings','any_symbols','any_units','any_equations'):
                v = m.get(k)
                if isinstance(v, str):
                    m[k] = [v]
                elif isinstance(v, list):
                    m[k] = [str(x) for x in v]
                else:
                    m[k] = []
            r['match'] = m
        elif isinstance(m, str):
            r['match'] = [m]
        elif isinstance(m, list):
            r['match'] = [str(x) for x in m]
        else:
            r['match'] = []
        tf = r.get('transform', {})
        tags = tf.get('add_tags', [])
        if isinstance(tags, str):
            tf['add_tags'] = [tags]
        elif isinstance(tags, list):
            tf['add_tags'] = [str(x) for x in tags]
        else:
            tf['add_tags'] = []
        r['transform'] = tf
    return rs


def claim_text_from(obj: Dict[str, Any]) -> str:
    for k in ('claim_text', 'text', 'statement', 'raw_line'):
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return json.dumps(obj, ensure_ascii=False)


def apply_rules(obj: Dict[str, Any], rulesets: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Determine claim text and infer layout noise if missing
    text_raw = claim_text_from(obj)
    norm = obj.get('normalized_text')
    if not isinstance(norm, str):
        s = text_raw.strip().lower()
        norm = re.sub(r"\s+", " ", s)
    # Ensure extracted features exist (do not overwrite if already present)
    # symbols: curated greek/math tokens
    def _as_list(v):
        return v if isinstance(v, list) else None
    existing_symbols = _as_list(obj.get('extracted_symbols'))
    existing_units = _as_list(obj.get('extracted_units'))
    existing_equations = _as_list(obj.get('extracted_equations'))
    existing_constants = _as_list(obj.get('extracted_constants'))
    existing_moduli = _as_list(obj.get('extracted_moduli'))
    existing_ops = _as_list(obj.get('extracted_ops'))

    SYMBOLS = [
        "λ", "ω", "θ", "Δ", "∑", "∫", "μ", "α", "β", "γ", "Ω", "η", "κ", "π", "χ", "φ", "ψ", "τ", "σ"
    ]
    if existing_symbols is None:
        sym_hits = sorted({s for s in SYMBOLS if s in text_raw})
    else:
        sym_hits = sorted({str(s) for s in existing_symbols})

    # units: conservative regex boundary matching (mirror claims builder)
    def extract_units(text_raw: str) -> List[str]:
        t = text_raw
        hits = set()
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

    if existing_units is None:
        unit_hits = extract_units(text_raw)
    else:
        unit_hits = sorted({str(u) for u in existing_units})

    # equations: short snippets around '=' or '≈', normalized whitespace, max ~60 chars
    if existing_equations is None:
        eq_hits = []
        for m in re.finditer(r"[=≈]", text_raw):
            start = max(0, m.start() - 30)
            end = min(len(text_raw), m.end() + 30)
            snippet = text_raw[start:end]
            snippet = re.sub(r"\s+", " ", snippet.strip())
            if 1 <= len(snippet) <= 60:
                eq_hits.append(snippet)
        eq_hits = sorted(set(eq_hits))
    else:
        eq_hits = sorted({str(s) for s in existing_equations})

    # constants (mirror builder)
    def extract_constants(text_raw: str) -> List[str]:
        hits = set()
        for sym in ["π", "φ", "τ", "ℏ", "ħ"]:
            if sym in text_raw:
                hits.add(sym)
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

    if existing_constants is None:
        const_hits = extract_constants(text_raw)
    else:
        const_hits = sorted({str(s) for s in existing_constants})

    # moduli (mirror builder)
    def extract_moduli(text_raw: str) -> List[str]:
        hits = set()
        for m in re.finditer(r"(?i)\bmod\s*(\d{1,4})\b", text_raw):
            hits.add(f"mod {m.group(1)}")
        for m in re.finditer(r"≡\s*\(\s*mod\s*(\d{1,4})\s*\)", text_raw):
            hits.add(f"mod {m.group(1)}")
        for m in re.finditer(r"(?<!\S)%\s*(\d{1,4})\b", text_raw):
            hits.add(f"mod {m.group(1)}")
        return sorted(hits)

    if existing_moduli is None:
        mod_hits = extract_moduli(text_raw)
    else:
        mod_hits = sorted({str(s) for s in existing_moduli})

    # ops (mirror builder)
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

    if existing_ops is None:
        op_hits = extract_ops(text_raw)
    else:
        op_hits = sorted({str(s) for s in existing_ops})

    existing_layout_tags = obj.get('layout_tags') if isinstance(obj.get('layout_tags'), list) else []
    noise_flag = obj.get('is_layout_noise') if isinstance(obj.get('is_layout_noise'), bool) else None

    inferred_tags: List[str] = []
    if noise_flag is None:
        # Apply conservative heuristics mirroring claims builder
        if not norm:
            inferred_tags.append('layout:empty')
        if norm and len(norm) < 5:
            inferred_tags.append('layout:short')
        ns = ''.join(ch for ch in text_raw if not ch.isspace())
        if ns:
            alnum = sum(ch.isalnum() for ch in ns)
            if alnum / max(1, len(ns)) < 0.3:
                inferred_tags.append('layout:nonalnum-heavy')
        suspicious = ['\u200b', '\u200c', '\ufeff', '•', '·', '▪', '—', '–', '□']
        glyph_hits = sum(text_raw.count(x) for x in suspicious)
        if glyph_hits >= 2:
            inferred_tags.append('layout:glyphs')
    # Decide final noise and tags without overwriting existing ones
    final_layout_tags = existing_layout_tags if existing_layout_tags else sorted(set(inferred_tags))
    final_is_noise = (noise_flag if noise_flag is not None else bool(final_layout_tags))

    text_ci = text_raw.lower()
    hits = []
    tags: List[str] = []
    recs: List[str] = []
    # Quarantine layout noise: do not apply physics rules
    if final_is_noise:
        tags = sorted(set((obj.get('model_tags') or []) + ['TXT:layout_noise']))
        out = {
            "id": obj.get("id"),
            "kind": obj.get("kind"),
            "text": obj.get("text"),
            "normalized_text": obj.get("normalized_text"),
            "source_span": obj.get("source_span"),
            "rule_hits": [],
            "model_tags": tags,
            "recommended_rewrites": [],
            "is_layout_noise": True,
            "layout_tags": final_layout_tags,
            "extracted_symbols": sym_hits,
            "extracted_units": unit_hits,
            "extracted_equations": eq_hits,
            "extracted_constants": const_hits,
            "extracted_moduli": mod_hits,
            "extracted_ops": op_hits,
        }
        for k in sorted(obj.keys()):
            if k in out:
                continue
            out[k] = obj[k]
        return out
    for rs in rulesets:
        rs_id = rs.get('as_above', {}).get('ruleset_id') or rs.get('so_below', {}).get('version', 'unknown')
        for r in rs.get('as_above', {}).get('rules', []):
            rid = r.get('id')
            match = r.get('match', [])
            matched = False
            if isinstance(match, list):
                for needle in match:
                    if needle.lower() in text_ci:
                        matched = True
                        break
            elif isinstance(match, dict):
                # any_substrings
                subs = match.get('any_substrings', [])
                if not matched:
                    for needle in subs:
                        if needle.lower() in text_ci:
                            matched = True
                            break
                # any_symbols
                if not matched:
                    sym_needles = set(match.get('any_symbols', []))
                    sym_hitset = set(sym_hits)
                    if sym_needles & sym_hitset:
                        matched = True
                # any_units
                if not matched:
                    unit_needles = {u.lower() for u in match.get('any_units', [])}
                    unit_hitset = {u.lower() for u in unit_hits}
                    if unit_needles & unit_hitset:
                        matched = True
                # any_equations (substring over extracted snippets)
                if not matched:
                    eq_needles = [s.lower() for s in match.get('any_equations', [])]
                    eq_snips = [s.lower() for s in eq_hits]
                    if any(any(n in sn for sn in eq_snips) for n in eq_needles):
                        matched = True
                # any_constants
                if not matched:
                    const_needles = {s if s in ["π","φ","τ","ℏ","ħ"] else s.lower() for s in match.get('any_constants', [])}
                    const_hitset = {s if s in ["π","φ","τ","ℏ","ħ"] else s.lower() for s in const_hits}
                    if const_needles & const_hitset:
                        matched = True
                # any_moduli
                if not matched:
                    mod_needles = {s.lower() for s in match.get('any_moduli', [])}
                    mod_hitset = {s.lower() for s in mod_hits}
                    if mod_needles & mod_hitset:
                        matched = True
                # any_ops
                if not matched:
                    op_needles = {s.lower() for s in match.get('any_ops', [])}
                    op_hitset = {s.lower() for s in op_hits}
                    if op_needles & op_hitset:
                        matched = True
                # any_constants
                if not matched:
                    const_needles = {s.lower() for s in match.get('any_constants', [])}
                    const_hitset = {s if s in ["π","φ","τ","ℏ","ħ"] else s.lower() for s in const_hits}
                    if const_needles & const_hitset:
                        matched = True
                # any_moduli
                if not matched:
                    mod_needles = {s.lower() for s in match.get('any_moduli', [])}
                    mod_hitset = {s.lower() for s in mod_hits}
                    if mod_needles & mod_hitset:
                        matched = True
                # any_ops
                if not matched:
                    op_needles = {s.lower() for s in match.get('any_ops', [])}
                    op_hitset = {s.lower() for s in op_hits}
                    if op_needles & op_hitset:
                        matched = True
            if matched:
                hits.append({"ruleset_id": rs_id, "rule_id": rid})
                tags.extend(r.get('transform', {}).get('add_tags', []))
                rr = r.get('transform', {}).get('recommended_rewrite')
                if isinstance(rr, str) and rr.strip():
                    recs.append(rr.strip())
    # Deduplicate + sort tags
    tags = sorted(set(tags))
    # Deterministic output: build in fixed key order
    out = {
        "id": obj.get("id"),
        "kind": obj.get("kind"),
        "text": obj.get("text"),
        "normalized_text": obj.get("normalized_text"),
        "source_span": obj.get("source_span"),
        "rule_hits": hits,
        "model_tags": tags,
        "recommended_rewrites": sorted(set(recs)),
        "is_layout_noise": False if noise_flag is None else bool(noise_flag),
        "layout_tags": existing_layout_tags if existing_layout_tags else final_layout_tags,
        "extracted_symbols": sym_hits,
        "extracted_units": unit_hits,
        "extracted_equations": eq_hits,
        "extracted_constants": const_hits,
        "extracted_moduli": mod_hits,
        "extracted_ops": op_hits,
    }
    # Carry over any other original keys without timestamps, in stable order
    for k in sorted(obj.keys()):
        if k in out:
            continue
        out[k] = obj[k]
    return out


def write_ledger(paths: List[str]) -> None:
    ts = utc_now_iso()
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8") as f:
        for p in paths:
            f.write(f"{sha256_file(p)}  {p}  {ts}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply physics corrections")
    parser.add_argument("--claims", default=CLAIMS_PATH, help="Path to claims.latest.jsonl")
    args = parser.parse_args()
    if not os.path.exists(SPEC_PATH):
        print(f"Spec not found: {SPEC_PATH}", file=sys.stderr)
        return 2

    rule_paths = [p for p,_ in RULE_ORDER]
    require_rules_exist(rule_paths)
    ensure_claims_exists(args.claims)

    # Load rules in fixed order
    rulesets = [load_ruleset(p) for p,_ in RULE_ORDER]

    os.makedirs(os.path.dirname(OUT_JSONL), exist_ok=True)
    written = 0
    with open(args.claims, 'r', encoding='utf-8', errors='replace') as fin, \
         open(OUT_JSONL, 'w', encoding='utf-8') as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            out = apply_rules(obj, rulesets)
            fout.write(json.dumps(out, ensure_ascii=False) + "\n")
            written += 1

    ledger_paths = [args.claims, *rule_paths, OUT_JSONL]
    write_ledger(ledger_paths)

    print(f"Corrections written: {OUT_JSONL} (count={written})\nLedger: {LEDGER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
