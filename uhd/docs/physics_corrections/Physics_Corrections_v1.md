# Physics Corrections v1 (Scaffold)

This stage is where CCR, QPhiD, QGC, and Angle Clock corrections are applied to the Physics Claims index.

- Inputs:
  - Local-only claims output: `uhd/receipts/physics_claims/claims.latest.jsonl` (produced by `physics_extract_text.py` then `physics_claims_build.py`).
  - Tracked rule specs:
    - `uhd/spec/physics_corrections/CCR_Core_Axioms_v1.json`
    - `uhd/spec/physics_corrections/QPhiD_Rules_v1.json`
    - `uhd/spec/physics_corrections/QGC_Rules_v1.json`
    - `uhd/spec/physics_corrections/AngleClock_Model_v1.json`
- Outputs (local-only receipts; ignored by Git):
  - `uhd/receipts/physics_corrections/corrections.latest.jsonl`
  - `uhd/receipts/physics_corrections/corrections.ledger.txt`

Run
```bash
python3 uhd/scripts/physics_corrections_apply.py
```

Notes
- If claims are missing, the script prints a clear message to run the prior stages.
- This scaffold performs a pass-through, tagging each claim with `correction_status: unprocessed`.

## Authoring CCR rules (v1)

The tracked rule specs under `uhd/spec/physics_corrections/` are where you encode
CCR/QPhiD/QGC/AngleClock into machine-actionable rules.

For CCR Core Axioms:
- File: `uhd/spec/physics_corrections/CCR_Core_Axioms_v1.json`
- Each rule includes:
  - `id` (stable, deterministic sort key)
  - `match.any_keywords` (case-insensitive substring triggers)
  - `transform` (currently `annotate_only` until rewrite transforms are formalized)
  - `receipt_requirements.required` (what must exist to accept/correct the claim)

The apply script currently produces deterministic `rule_hits` for each claim and
writes local-only outputs under `uhd/receipts/physics_corrections/` (ignored by Git).

## QGG/QGL rule format
- Rulesets live under `uhd/spec/physics_corrections/` with CCR-style actionable format.
- Top-level keys: `as_above` / `so_below`.
- `as_above` fields: `version`, `ruleset_id`, `purpose`, `nonnegotiables`, `rule_format`, `rules[]`.
- Each rule: `id`, `name`, `statement`, `match` (case-insensitive substring over claim_text), `transform` (with `add_tags` list and optional `recommended_rewrite`), and `receipt_requirements` (non-empty list).
- Current tracked rulesets: `QGG_Rules_v1.json` and `QGL_Rules_v1.json`.

## Extended match object keys
Rules may use a match-object with these keys in addition to plain substring lists:
- `any_substrings`: case-insensitive substring over claim text
- `any_symbols`: exact token match against `extracted_symbols`
- `any_units`: case-insensitive token match against `extracted_units`
- `any_equations`: case-insensitive substring over `extracted_equations` snippets
- `any_constants`: match against `extracted_constants` (latin tokens by case-insensitive text; unicode symbols exact)
- `any_moduli`: case-insensitive token match against `extracted_moduli`
- `any_ops`: case-insensitive token match against `extracted_ops`

All matching is deterministic and side-effect free. Noise (`is_layout_noise`) is quarantined and not passed through physics rulesets.

To add a rule
1. Pick a unique `id` and add a descriptive `name` and `statement`.
2. Add one or more `match` substrings.
3. Add `transform.add_tags` with new or existing domain tags.
4. Keep `receipt_requirements` non-empty (e.g., `["hit"]`).
