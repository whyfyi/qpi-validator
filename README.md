# QPI (Quantum Prime Insights) — Validator Repo (Ready to Push)

## What this repo contains
- A **Python validator** that independently checks the **Twin Prime Midpoint Law** up to a finite bound N.
- A **Lean 4 skeleton** that formalizes definitions and the midpoint equivalence statement (with TODO proofs).
- A **publication split**: Paper 1 (proven finite statements + receipts) vs Paper 2 (conjectures + evidence).
- **Receipts** (JSON + SHA-256) for N=1e6, 1e7, 1e8 generated in this environment.

## What this repo does NOT claim
- This repo does **not** prove infinitely many twin primes.
- Computation cannot prove an infinite claim; it can only produce receipts up to finite N.

## Receipts produced here
| N | twin_pairs | twin_pairs(p≥7) | red_cells | diff(red - twin(p≥7)) | sha256 |
|---:|---:|---:|---:|---:|---|
| 1000000 | 8169 | 8167 | 8167 | 0 | `fbc16732c8694cb5adefae0aa89d1d175198a23e5da1242fd97575cb9f2e5038` |
| 10000000 | 58980 | 58978 | 58978 | 0 | `41f75c003541e043e7bfba905cae5952d42832c141bb945a4d8fa08171179dca` |
| 100000000 | 440312 | 440310 | 440310 | 0 | `1e420ac790b3e56a884162c437118a6757ed1a22e69a42df27388af88d6120fb` |

See `results/checksums.txt` for the canonical hashes.

## Run the validator yourself
```bash
python3 python/qpi_validate.py --N 100000000 --out results/validation_100000000.json
```

## Notes on the Rust file you pasted
Your pasted segmented wheel-sieve draft has **indexing issues** (segment offsets vs mod-30 residues) that can silently corrupt counts.
This repo includes `src/qpi_sieve_fixed.rs` with corrected indexing strategy and explicit correctness checks.

## Folder layout
```
qpi_validator_repo/
├── python/
│   └── qpi_validate.py
├── src/
│   └── qpi_sieve_fixed.rs
├── lean/
│   └── qpi_theorems_clean.lean
├── papers/
│   ├── paper1_proven.tex
│   └── paper2_conjecture.tex
└── results/
    ├── validation_*.json
    └── checksums.txt
```
