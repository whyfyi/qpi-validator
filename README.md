# QPI (Quantum Prime Insights) — Validator Repo
## Milestones
- **1e13 twin prime receipt (v1.1.0-1e13):** https://github.com/whyfyi/qpi-validator/releases/tag/v1.1.0-1e13


This repository publishes **finite, reproducible receipts** for the QPI color-sieve / midpoint framework:
- a Python validator for the **Twin Prime Midpoint Law** (finite N),
- independent **twin-prime count receipts via primesieve** (fast baseline to large N),
- papers + visuals that explain the **modular lattice / spiral / helix** presentation,
- canonical SHA-256 checksums so results can be verified without trust.

> Integrity rule: **Theorems (finite / proven by receipts) are separated from Conjectures (infinite claims).**

---

## What is validated here (finite receipts)

### A) QPI Midpoint-Law receipts (Python validator)
For a chosen bound **N**, `python/qpi_validate.py` produces `results/validation_<N>.json` and prints `LAW: PASS` when the implementation finds **no counterexamples** within that finite range.

**Included receipts**
- `results/validation_1000000.json`
- `results/validation_10000000.json`
- `results/validation_100000000.json`
- `results/validation_1000000000.json`

### B) Independent twin-prime count receipts (primesieve)
`primesieve` is an external, highly-optimized sieve tool. This repo records its output as an **independent baseline**.

- `results/primesieve_twin_counts.json` (counts for 1e9, 1e10, 1e12 + CPU info)

This does **not** prove infinity; it provides a fast, verifiable count baseline.

#### Primesieve 1e12 receipt (GitHub Actions)

A full twin-prime count to **N = 1e12** was generated on neutral infrastructure and recorded as a reproducible receipt:

- Tool: `primesieve`
- Mode: twin-prime count (`-c2`)
- Upper bound: `1000000000000`
- Runner: GitHub Actions (`ubuntu-latest`)
- Generated (UTC): `2025-12-24`
- Receipt: `results/primesieve_twin_count_1000000000000.json`
- Integrity: verified via `results/checksums.txt` (SHA-256)

This receipt was produced via a manual `workflow_dispatch` run using the canonical
`.github/workflows/primesieve_receipt_dispatch.yml` workflow. Anyone can reproduce
the run or independently verify the hash without trusting the authors.

---

## What is NOT claimed
- This repo does **not** prove infinitely many twin primes.
- Computation cannot prove an infinite claim; it can only produce receipts up to finite N.
- “Yellow candidate midpoints exist infinitely often” is a modular fact.
- “Infinitely many candidates become red (both neighbors prime)” remains a **Conjecture** unless proven.

---

## Visual and paper assets
Assets are included to document the **modular / geometric presentation** of the sieve:

- `assets/qpi_spiral_twinprime_v3.6.png`
- `assets/9_wide_Helix.png`
- `assets/Mod_9_Double_Helix_DNA_Flow.png`

Papers (PDF):
- `papers/Quantum_Prime_Insight.pdf`
- `papers/Quantum_Prime_Insight_Infinite_Primes_and_Twin_Primes.pdf`
- `papers/Quantum_Prime_Insight_Harmonic_Lattice_Law_of_Infinite_Primes_and_Twin_Primes.pdf`

These visuals are **representations of modular structure** (e.g., residues / digital roots / periodic filters). They support explanation and pattern-auditing; proofs still require discrete-number statements.

---

## Canonical checksums (do not trust, verify)
The authoritative hashes live in:
- `results/checksums.txt`

Rebuild canonically:
```bash
bash scripts/rebuild_checksums.sh
## UQHD (Universal Quantum Hard Drive)

This repo includes a **verifiable anchor-map receipt** layer (UQHD v0.1):
- Spec: `uhd/spec/UQHD_memory_prompt_v0.1.json`
- Doc: `uhd/docs/uqhd_anchor_map_v0.1.md`
- Receipt: `uhd/receipts/uqhd_anchor_map_1e13.json`

CI verifies:
- `results/checksums.txt`
- UQHD anchor-map integrity + Merkle root
- `uhd/receipts/checksums.txt`

