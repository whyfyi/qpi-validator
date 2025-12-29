from __future__ import annotations
import json
import sys
from pathlib import Path

from uqhd_lib import sha256_hex, canonical_json_bytes, merkle_root_sha256_hex

def main(p: str):
    path = Path(p)
    obj = json.loads(path.read_text(encoding="utf-8"))

    integ = obj.get("integrity") or {}
    if integ.get("method") != "sha256":
        raise SystemExit("FAIL: integrity.method != sha256")

    obj2 = dict(obj)
    obj2.pop("integrity", None)
    digest = sha256_hex(canonical_json_bytes(obj2))
    if integ.get("digest") != digest:
        raise SystemExit("FAIL: integrity.digest mismatch")

    leaf_hashes = [x["leaf_sha256"] for x in obj["anchors"]["leaves"]]
    root = merkle_root_sha256_hex(leaf_hashes)
    if root != obj["merkle"]["root_sha256"]:
        raise SystemExit("FAIL: merkle root mismatch")

    print("OK:", p)
    print("merkle_root_sha256:", root)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 scripts/uqhd_verify_anchor_map.py <file>")
    main(sys.argv[1])

