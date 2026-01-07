# Physics Claims v1

This stage builds a structured claims index from the extracted Halliday text.

- Upstream extractor: `uhd/scripts/physics_extract_text.py` writes `uhd/receipts/physics/halliday_cheatsheet.latest.txt`.
- Spec: `uhd/spec/physics_claims/Physics_Claims_Spec_v1.json`
- Schema: `uhd/schemas/physics_claims/physics_claims_spec_v1.schema.json`
- Builder: `uhd/scripts/physics_claims_build.py`
- Outputs (local receipts; not committed):
  - `uhd/receipts/physics_claims/claims.latest.jsonl`
  - `uhd/receipts/physics_claims/claims.extract.latest.txt`
  - `uhd/receipts/physics_claims/claims.ledger.txt`

Run
```bash
python3 uhd/scripts/physics_claims_build.py \
  --input uhd/receipts/physics/halliday_cheatsheet.latest.txt \
  --max-lines 200000
```

Notes
- The builder uses simple heuristics to classify lines as `equation|definition|constant|unit|note|other`.
- Receipts include sha256 for the input text and both output files.

## Layout/noise flags
Each output line now includes two additional fields:
- `is_layout_noise` (boolean): true for lines likely from PDF layout artifacts (empty, very short, mostly non‑alphanumeric, or glyph‑heavy).
- `layout_tags` (list of strings): stable tags explaining which heuristic triggered (e.g., `layout:short`, `layout:glyphs`).

Physics corrections quarantine these lines (tagged `TXT:layout_noise`) and skip applying domain rules, preserving auditability.

## Extracted features
Each JSON object also includes conservative, deterministic feature lists used by downstream rules:
- `extracted_symbols` (list of strings): curated Greek/math symbols present in raw text (e.g., λ, ω, θ, Δ, ∑, ∫, μ, …).
- `extracted_units` (list of strings): unit tokens via boundary-checked regex. Canonical forms: `Hz`, `Pa`, and lowercase `kg`, `mol`, `cd`, `rad`, `rad/s`, `m/s`, `m/s^2`.
- `extracted_equations` (list of strings): short snippets around `=` or `≈` (≤ ~60 chars), whitespace-normalized.
- `extracted_constants` (list of strings): constants by word-boundary (latin) or direct symbol checks (unicode). Examples: `pi`, `phi`, `tau`, `e`, `c`, `G`, `h`, and symbols `π`, `φ`, `τ`, `ℏ`, `ħ`.
- `extracted_moduli` (list of strings): canonical modular forms such as `mod 6`, `mod 30` (from `mod N`, `≡ (mod N)`, or standalone `% N`).
- `extracted_ops` (list of strings): calculus/geometry operator presence mapped to canonical tokens: `integral`, `sum`, `delta`, `derivative`, `partial`, `nabla`.
