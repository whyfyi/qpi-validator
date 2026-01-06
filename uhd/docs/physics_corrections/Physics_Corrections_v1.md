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
