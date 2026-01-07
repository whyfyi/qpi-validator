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

## Table of Contents
- [Overview](#overview)
- [Quickstart (deterministic)](#quickstart-deterministic)
- [Repo Map](#repo-map)
- [UHD Deterministic Corrections Pipeline](#uhd-deterministic-corrections-pipeline)
- [Rule Sets](#rule-sets)
- [Docs](#docs)
- [Using with LLM Reviewers (DeepExplain)](#using-with-llm-reviewers-deepexplain)
- [Disclaimers](#disclaimers)

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
```

## UQHD (Universal Quantum Hard Drive)

This repo includes a **verifiable anchor-map receipt** layer (UQHD v0.1):
- Spec: `uhd/spec/UQHD_memory_prompt_v0.1.json`
- Doc: `uhd/docs/uqhd_anchor_map_v0.1.md`
- Receipt: `uhd/receipts/uqhd_anchor_map_1e13.json`

CI verifies:
- `results/checksums.txt`
- UQHD anchor-map integrity + Merkle root
- `uhd/receipts/checksums.txt`

---

## Overview

QPI Validator provides finite, reproducible receipts for prime-pattern claims and a deterministic UHD (Universal/Unified Heuristic/Hybrid Deterministic) subsystem used for tagging and structured analysis. The `uhd/` subtree contains a small, audit-friendly pipeline that turns local text into claims, applies tracked rule sets deterministically, and writes local-only receipts (ignored by Git).

UHD is built for auditability: stable ordering, no timestamps embedded in JSONL/Markdown content, and explicit receipts that carry timestamps only in ledger files under `uhd/receipts/` (which are not committed).

## Quickstart (deterministic)

Compile scripts and run the smoketest. This writes only to `uhd/receipts/` (local, untracked by Git):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile uhd/scripts/*.py
python3 uhd/scripts/physics_smoketest.py
```

Generated artifacts land under `uhd/receipts/` and must not be committed.

## Repo Map

- `python/` — QPI finite validators and helpers (prime-related).
- `results/` — published finite receipts and checksums for QPI validators.
- `assets/`, `papers/` — visuals and explanatory PDFs.
- `uhd/` — deterministic tagging/corrections pipeline (local-only receipts). See `uhd/README.md`.
  - `uhd/spec/` — tracked JSON specs and rules (e.g., CCR/QGC/QPhiD/QGG/QGL/AngleClock).
  - `uhd/schemas/` — JSON Schemas for UHD specs.
  - `uhd/docs/` — UHD documentation.
  - `uhd/scripts/` — deterministic UHD scripts (claims build, apply corrections, report, smoketest).
  - `uhd/fixtures/` — falsification-friendly synthetic inputs used by the smoketest.
  - `uhd/receipts/` — generated receipts/outputs (ignored by Git).

## UHD Deterministic Corrections Pipeline

High level flow:
- Claims build: parse local text into JSONL claims with normalized text and extracted features.
- Corrections apply: run tracked rule sets deterministically, producing `rule_hits`, `model_tags`, and optional `recommended_rewrites` (cautious, interpretive suggestions).
- Report: aggregate counts, top tags, and top entries for quick review.
- Fixtures + smoketest: run on curated synthetic inputs to exercise tags and guard precision.

Determinism and quarantine:
- Layout-noise is detected conservatively and quarantined (`TXT:layout_noise`); physics/domain rules are not applied to these lines.
- Matching is deterministic with stable ordering; JSONL/Markdown content embeds no timestamps.

## Rule Sets

Tracked UHD rules (JSON):
- `uhd/spec/physics_corrections/QGL_Rules_v1.json`
- `uhd/spec/physics_corrections/QGG_Rules_v1.json`
- `uhd/spec/physics_corrections/CCR_Core_Axioms_v1.json`
- `uhd/spec/physics_corrections/QGC_Rules_v1.json`
- `uhd/spec/physics_corrections/QPhiD_Rules_v1.json`
- `uhd/spec/physics_corrections/AngleClock_Rules_v1.json`

Related semantic maps:
- `uhd/spec/whyfyi_os/WhyFYI_OS_Term_Map_v1.json`
- `uhd/docs/whyfyi_os/WhyFYI_OS_Domain_Map_v1.md`

## Docs

- `uhd/docs/physics_claims/Physics_Claims_v1.md` — claims index structure, features, and layout-noise notes.
- `uhd/docs/physics_corrections/Physics_Corrections_v1.md` — correction pipeline, rule formats, and extended match-object keys.

## Using with LLM Reviewers (DeepExplain)

Recommended reading order for LLM reviewers and humans alike:
1) `README.md` (this file) — repo overview and navigation.
2) `uhd/README.md` — UHD navigation hub.
3) UHD docs — `uhd/docs/physics_claims/Physics_Claims_v1.md`, `uhd/docs/physics_corrections/Physics_Corrections_v1.md`.
4) Fixtures — `uhd/fixtures/*.jsonl` for falsification-friendly tests.
5) Rules — `uhd/spec/physics_corrections/*.json` to audit deterministic tagging behavior.

Emphasis:
- Fixtures are falsification-friendly to surface over-tagging.
- Smoketest is deterministic and validates outputs byte-for-byte.
- Use “model framing / interpretive mapping / candidate” language; do not infer claims of empirical proof.

## Disclaimers

- UHD semantic layers and mappings are **interpretive** and used for tagging/simulation context. They are **not** claims about physical reality.
- Outputs are deterministic; timestamps appear only in local receipt ledgers under `uhd/receipts/` (not committed).

