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
