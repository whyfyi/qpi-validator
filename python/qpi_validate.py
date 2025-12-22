#!/usr/bin/env python3
"""
qpi_validate.py
Independent validator for QPI Twin Prime Midpoint Law.

What this script proves (computationally):
- For a finite bound N, it verifies:
  red_cells(N) == twin_pairs_with_p_ge_7(N)
where:
  twin pair = (p, p+2) primes
  red cell midpoint m = p+1 is "yellow" and both neighbors are prime
  yellow(m) := (m % 3 == 0) and (m % 10 in {0,2,8})

Important:
- This script does NOT prove the Twin Prime Conjecture (infinitely many twin primes).
- It only produces receipts up to the chosen finite N.

Usage:
  python3 qpi_validate.py --N 100000000 --out results/validation_1e8.json
"""
from __future__ import annotations
import argparse, json, hashlib, math, time, platform, sys
from dataclasses import asdict, dataclass

def sieve_odd(n: int) -> bytearray:
    """Odd-only sieve: is_prime[i] corresponds to (2*i+1)."""
    if n < 2:
        return bytearray()
    size = n // 2 + 1
    is_prime = bytearray(b"\x01") * size
    is_prime[0] = 0  # 1 not prime
    limit = int(math.isqrt(n))
    for p in range(3, limit + 1, 2):
        if is_prime[p // 2]:
            start = p * p
            step = 2 * p
            for x in range(start, n + 1, step):
                is_prime[x // 2] = 0
    return is_prime

def is_prime_from_sieve(is_prime_odd: bytearray, x: int) -> bool:
    if x == 2:
        return True
    if x < 2 or (x % 2 == 0):
        return False
    return bool(is_prime_odd[x // 2])

def is_yellow(m: int) -> bool:
    return (m % 3 == 0) and (m % 10 in (0, 2, 8))

@dataclass(frozen=True)
class QPIReceipt:
    N: int
    sieve_seconds: float
    count_seconds: float
    total_seconds: float
    twin_pairs: int
    twin_pairs_p_ge_7: int
    red_cells: int
    diff_red_minus_twins_p_ge_7: int
    platform: str
    python: str

def validate(N: int) -> QPIReceipt:
    t0 = time.time()
    is_prime_odd = sieve_odd(N)
    t1 = time.time()

    twin_pairs = 0
    twin_pairs_p_ge_7 = 0
    for p in range(3, N - 1, 2):
        if is_prime_odd[p // 2] and is_prime_from_sieve(is_prime_odd, p + 2):
            twin_pairs += 1
            if p >= 7:
                twin_pairs_p_ge_7 += 1

    red_cells = 0
    for m in range(0, N + 1):
        if is_yellow(m):
            if m - 1 >= 2 and m + 1 <= N:
                if is_prime_from_sieve(is_prime_odd, m - 1) and is_prime_from_sieve(is_prime_odd, m + 1):
                    red_cells += 1

    t2 = time.time()
    return QPIReceipt(
        N=N,
        sieve_seconds=t1 - t0,
        count_seconds=t2 - t1,
        total_seconds=t2 - t0,
        twin_pairs=twin_pairs,
        twin_pairs_p_ge_7=twin_pairs_p_ge_7,
        red_cells=red_cells,
        diff_red_minus_twins_p_ge_7=red_cells - twin_pairs_p_ge_7,
        platform=platform.platform(),
        python=sys.version.replace("\n", " "),
        )

def sha256_json(obj: dict) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--out", type=str, required=True)
    args = ap.parse_args()

    receipt = validate(args.N)
    d = asdict(receipt)
    d["checksum_sha256"] = sha256_json(d)

    ok = (receipt.diff_red_minus_twins_p_ge_7 == 0)
    d["midpoint_law_holds_for_p_ge_7"] = bool(ok)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, sort_keys=True)

    print("WROTE:", args.out)
    print("CHECKSUM:", d["checksum_sha256"])
    print("LAW:", "PASS" if ok else "FAIL")
    if not ok:
        print("DIFF red - twin(p>=7):", receipt.diff_red_minus_twins_p_ge_7)

if __name__ == "__main__":
    main()
