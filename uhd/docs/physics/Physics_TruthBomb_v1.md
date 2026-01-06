# Physics TruthBomb v1

Physics TruthBomb v1 validates a dual-notation spec (as_above / so_below) for a single local PDF artifact and records SHA-256 receipts.

- Spec: `uhd/spec/physics/Physics_Corpus_Spec_v1.json`
- Schema: `uhd/schemas/physics/physics_corpus_spec_v1.schema.json`
- Validator: `uhd/scripts/physics_corpus_validate.py`
- Receipts: `uhd/receipts/physics/checksums.latest.txt`, `uhd/receipts/physics/checksums.ledger.txt`
- The PDF may be a symlink or local copy; PDFs are NOT committed.

## Stage the PDF locally
Expected artifact path (inside this repo):

```
uhd/imports/physics/Halliday_Cheatsheet.pdf
```

Recommended: symlink from the actual file location into the above path.

## Run the validator
```bash
python3 uhd/scripts/physics_corpus_validate.py \
  --spec uhd/spec/physics/Physics_Corpus_Spec_v1.json
```

## What the validator does
- Validates the spec structure and required values.
- Computes SHA-256 for the declared artifact path.
- Overwrites `checksums.latest.txt` with the most recent hash line.
- Appends a ledger entry to `checksums.ledger.txt` as:

```
<sha256>  <path>  <utc_iso8601>
```

No external dependencies; standard library only.
