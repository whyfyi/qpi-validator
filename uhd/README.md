# UHD — Deterministic Tagging/Corrections (Navigation Hub)

UHD is a small, deterministic subsystem for local, auditable tagging and corrections. It parses local text into structured claims, applies tracked rule sets in a stable order, and writes local-only receipts under `uhd/receipts/` (ignored by Git).

Disclaimers
- UHD semantic layers and mappings are interpretive; they support tagging and simulation framing. They are not claims about physical reality.
- Outputs are deterministic; JSONL/Markdown content contains no timestamps. Timestamps appear only in local receipt ledgers.

Start here
- Scripts:
  - `uhd/scripts/physics_smoketest.py`
  - `uhd/scripts/physics_claims_build.py`
  - `uhd/scripts/physics_corrections_apply.py`
  - `uhd/scripts/physics_corrections_report.py`
- Specs / rules:
  - `uhd/spec/physics_corrections/CCR_Core_Axioms_v1.json`
  - `uhd/spec/physics_corrections/QGC_Rules_v1.json`
  - `uhd/spec/physics_corrections/QPhiD_Rules_v1.json`
  - `uhd/spec/physics_corrections/QGG_Rules_v1.json`
  - `uhd/spec/physics_corrections/QGL_Rules_v1.json`
  - `uhd/spec/physics_corrections/AngleClock_Rules_v1.json`
- Fixtures:
  - `uhd/fixtures/physics_claims_synthetic.jsonl`
  - `uhd/fixtures/physics_claims_noisy_synthetic.jsonl`
  - `uhd/fixtures/physics_claims_ccr_qgc_qphid_synthetic.jsonl`
- Docs:
  - `uhd/docs/physics_claims/Physics_Claims_v1.md`
  - `uhd/docs/physics_corrections/Physics_Corrections_v1.md`
  - `uhd/spec/whyfyi_os/WhyFYI_OS_Term_Map_v1.json`
  - `uhd/docs/whyfyi_os/WhyFYI_OS_Domain_Map_v1.md`

Determinism + auditability rules
- Stable ordering for rule evaluation and outputs.
- No timestamps inside JSONL/Markdown content.
- Receipts under `uhd/receipts/` are ignored by Git and remain local.
- PDFs must not be committed (see imports guidance in the physics pipeline).

Quickstart
```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile uhd/scripts/*.py
python3 uhd/scripts/physics_smoketest.py
```

