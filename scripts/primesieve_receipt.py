#!/usr/bin/env python3
import json, os, time, pathlib, subprocess, sys

def main():
    if len(sys.argv) != 2:
        print("Usage: primesieve_receipt.py <N>", file=sys.stderr)
        sys.exit(2)

    N = int(sys.argv[1])
    pathlib.Path("results").mkdir(parents=True, exist_ok=True)

    cpu_info = subprocess.check_output(["primesieve", "--cpu-info"], text=True).splitlines()
    out_line = subprocess.check_output(["bash", "-lc", f'primesieve -c2 1 {N} | tail -n 1'], text=True).strip()
    # expects: "Twin primes: 1870585220"
    twin_count = int(out_line.split(":")[1].strip())

    out = {
        "tool": "primesieve",
        "mode": "-c2",
        "N": N,
        "twin_primes_count": twin_count,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cpu_info": cpu_info,
    }

    json_path = pathlib.Path(f"results/primesieve_twin_count_{N}.json")
    json_path.write_text(json.dumps(out, indent=2) + "\n")

    sha = subprocess.check_output(["sha256sum", str(json_path)], text=True).strip()
    sha_path = pathlib.Path(f"results/primesieve_twin_count_{N}.sha256")
    sha_path.write_text(sha + "\n")

    print("WROTE:", json_path)
    print("SHA256:", sha)

if __name__ == "__main__":
    main()
