# UQHD Anchor Map Receipt v0.1

Derived receipt (integrity/provenance):
- sha256(file bytes) leaves, ordered
- sha256-merkle root over leaves
- integrity.digest = sha256(canonical JSON without integrity)

Verify:
1) sha256sum -c results/checksums.txt
2) python3 scripts/uqhd_verify_anchor_map.py uhd/receipts/uqhd_anchor_map_1e13.json
3) sha256sum -c uhd/receipts/checksums.txt

