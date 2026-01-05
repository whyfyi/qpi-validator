# Truth Bomb v2

Truth Bomb v2 is a minimal, auditable scaffold that validates a dual-notation spec (as_above / so_below) and records SHA-256 checksums for a fixed set of staged imports under `uhd/imports`.

Key points
- Spec file: `uhd/spec/truthbomb/TruthBomb_Spec_v2.json` (dual-notation)
- Schema: `uhd/schemas/truthbomb/truthbomb_spec_v2.schema.json`
- Validator: `uhd/scripts/truthbomb_validate.py` (stdlib only)
- Receipts: `uhd/receipts/truthbomb/checksums.txt`
- Imports may be symlinks; hashing resolves the actual file data.

Artifacts (fixed set)
- `uhd/imports/WhyFYI_5G.json`
- `uhd/imports/WhyFYI5G.json`
- `uhd/imports/DivineAlgebra_Master.json`
- `uhd/imports/QuantumManifestationMatrix_Master.json`
- `uhd/imports/GPAI_Conversation_Update_v1_1_5_2026_TimeStamp.txt`

How to run
1. Ensure the five staged imports exist at the above paths (symlinks are fine).
2. Run the validator:

   ```bash
   python3 uhd/scripts/truthbomb_validate.py \
     --spec uhd/spec/truthbomb/TruthBomb_Spec_v2.json
   ```

What it does
- Validates the spec structure and required values.
- Computes SHA-256 for each declared artifact path.
- Appends one line per artifact to `uhd/receipts/truthbomb/checksums.txt` in the format:

  ```
  <sha256>  <path>  <utc_iso8601>
  ```

Notes
- The validator uses only the Python standard library and performs no network access.
- Receipt appends are additive; remove lines manually if you need a clean slate.
