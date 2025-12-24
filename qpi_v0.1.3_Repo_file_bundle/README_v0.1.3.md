# QPI (Quantum Prime Insights) — Validator Repo

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
`primesieve` is an external, highly-optimized sieve tool. This repo records its output as an **independent baseline**:

- `results/primesieve_twin_counts.json` (counts for 1e9, 1e10, 1e12 + CPU info)

This does **not** prove infinity; it provides a fast, verifiable count baseline.

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

Verify all receipts:
```bash
sha256sum results/*.json
# compare to results/checksums.txt
```

---

## Reproduce: QPI validator (finite N)
```bash
python3 python/qpi_validate.py --N 1000000000 --out results/validation_1000000000.json
sha256sum results/validation_1000000000.json
```

---

## Reproduce: primesieve twin-prime counts
Install (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install -y primesieve-bin
```

Count twin primes (examples):
```bash
time primesieve -c2 1 1000000000
time primesieve -c2 1 10000000000
time primesieve -c2 1 1000000000000
```

Write receipt JSON (example script):
```bash
bash scripts/make_primesieve_receipt.sh
```

---

## Why primesieve is included (12th-grade explanation)
- Your QPI validator tests a specific rule by checking lots of numbers.
- Checking “is prime?” repeatedly can get slow at huge N.
- `primesieve` is optimized C++ sieving code designed exactly for large prime/twin-prime counting.
- So `primesieve` acts like an **independent measuring tool**:
  - QPI validator proves the rule holds up to a finite bound,
  - primesieve provides fast, verifiable twin-prime counts to large N as an external baseline.

---

## Repo layout
```
qpi_validator_repo/
├── assets/                        # PNG visuals (spiral/helix)
├── docs/                          # extra documentation from bundle
├── lean/                          # Lean 4 theorem skeletons
├── papers/                        # PDF papers
├── python/                         # Python validator
├── results/                        # JSON receipts + checksums.txt
├── scripts/                        # helper scripts (checksums, primesieve receipt)
└── src/                            # Rust experiments (optional)
```

---

## Security note (token hygiene)
Never store any GitHub token (PAT) inside this repo. If a token is ever committed, revoke it immediately.

---

## Citation
See `CITATION.cff` for machine-readable citation metadata.

---

## License
See `LICENSE.txt`.
