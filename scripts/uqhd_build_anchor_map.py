from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

from uqhd_lib import sha256_hex, canonical_json_bytes, merkle_root_sha256_hex

def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return ""

def utc_now_z() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

def load_epoch(path: Path):
    o = json.loads(path.read_text(encoding="utf-8"))
    t = o.get("twin_primes_count") or (o.get("results", {}) or {}).get("twin_prime_count")
    n = o.get("N") or (o.get("results", {}) or {}).get("n") or (((o.get("execution", {}) or {}).get("args", {}) or {}).get("n"))
    if t is None or n is None:
        raise SystemExit(f"Cannot read (n,twin_prime_count) from {path}")
    return int(n), int(t)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epoch", default="results/primesieve_twin_count_10000000000000.json")
    ap.add_argument("--bits", type=int, default=256)
    ap.add_argument("--out", default="uhd/receipts/uqhd_anchor_map_1e13.json")
    args = ap.parse_args()

    epoch_path = Path(args.epoch)
    out_path = Path(args.out)
    bound_n, twin_count = load_epoch(epoch_path)

    inputs = sorted([str(p) for p in Path("results").glob("*.json")])
    inputs = [p for p in inputs if p != str(out_path)]

    leaves = []
    leaf_hashes = []
    for i, p in enumerate(inputs):
        h = sha256_hex(Path(p).read_bytes())
        leaves.append({"anchor_id": i, "path": p, "leaf_sha256": h})
        leaf_hashes.append(h)

    root = merkle_root_sha256_hex(leaf_hashes)

    receipt = {
        "receipt_metadata": {
            "schema_version": "uqhd.anchor_map.v0.1",
            "generated_utc": utc_now_z(),
            "repository": {"name": "whyfyi/qpi-validator", "commit_hash": git_head()},
        },
        "epoch": {
            "bound_n": bound_n,
            "twin_prime_count": twin_count,
            "source_receipt_path": str(epoch_path),
        },
        "inputs": {
            "mode": "file_bytes_sha256",
            "paths": inputs,
            "hash_method": "sha256",
        },
        "anchors": {
            "bits_per_anchor": int(args.bits),
            "leaf_count": len(leaves),
            "leaves": leaves,
        },
        "merkle": {
            "method": "sha256_merkle_v0",
            "root_sha256": root,
            "leaf_hash_rule": "leaf_sha256 = sha256(file bytes)",
        },
    }

    digest = sha256_hex(canonical_json_bytes(receipt))
    receipt["integrity"] = {"method": "sha256", "digest": digest}

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    sha_path = out_path.with_suffix(".sha256")
    file_digest = sha256_hex(out_path.read_bytes())
    sha_path.write_text(f"{file_digest}  {out_path.name}\n", encoding="utf-8")

    print("WROTE:", out_path)
    print("WROTE:", sha_path)
    print("merkle_root_sha256:", root)

if __name__ == "__main__":
    main()

