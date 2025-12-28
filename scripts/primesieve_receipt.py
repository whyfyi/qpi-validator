#!/usr/bin/env python3
import hashlib
import json
import os
import pathlib
import platform
import subprocess
import sys
import time


def _sh(cmd, check=True, text=True):
    return subprocess.check_output(cmd, text=text) if check else subprocess.run(cmd, capture_output=True, text=text)


def _best_effort_cpu_model():
    # 1) primesieve --cpu-info (first line usually model string)
    try:
        lines = _sh(["primesieve", "--cpu-info"]).splitlines()
        for line in lines:
            if line.strip():
                return line.strip()
    except Exception:
        pass
    # 2) lscpu
    try:
        out = _sh(["bash", "-lc", "LC_ALL=C lscpu | grep -i 'Model name' | sed 's/.*: *//'"], text=True)
        out = out.strip()
        if out:
            return out
    except Exception:
        pass
    # 3) /proc/cpuinfo
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    # 4) macOS
    try:
        out = _sh(["sysctl", "-n", "machdep.cpu.brand_string"]).strip()
        if out:
            return out
    except Exception:
        pass
    return "unknown"


def _primesieve_version():
    try:
        return _sh(["primesieve", "--version"]).strip()
    except Exception:
        return "unknown"


def _git_commit_hash():
    try:
        return _sh(["git", "rev-parse", "HEAD"]).strip()
    except Exception:
        return "unknown"


def _repository_ref():
    # Prefer GitHub Actions env, else git remote, else CWD
    gh_repo = os.environ.get("GITHUB_REPOSITORY")
    if gh_repo:
        return gh_repo
    try:
        url = _sh(["git", "config", "--get", "remote.origin.url"]).strip()
        if url:
            return url
    except Exception:
        pass
    return os.getcwd()


def _ci_context():
    return {
        "workflow": os.environ.get("GITHUB_WORKFLOW", "local"),
        "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "actor": os.environ.get("GITHUB_ACTOR", "local"),
    }


def _environment_block():
    return {
        "os": platform.system() or "unknown",
        "kernel": platform.release() or "unknown",
        "arch": platform.machine() or "unknown",
        "cpu_model": _best_effort_cpu_model(),
        "python_version": sys.version.replace("\n", " "),
        "primesieve_version": _primesieve_version(),
    }


def _canonical_sha256(obj_without_integrity):
    data = json.dumps(obj_without_integrity, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return hashlib.sha256(data).hexdigest()


def main():
    if len(sys.argv) != 2:
        print("Usage: primesieve_receipt.py <N>", file=sys.stderr)
        sys.exit(2)

    N = int(sys.argv[1])
    pathlib.Path("results").mkdir(parents=True, exist_ok=True)

    # Measure execution wall clock
    cmd = ["bash", "-lc", f"primesieve -c2 1 {N} | tail -n 1"]
    t0 = time.perf_counter()
    out_line = _sh(cmd).strip()
    t1 = time.perf_counter()
    wall_time = t1 - t0

    # expects: "Twin primes: 1870585220"
    try:
        twin_count = int(out_line.split(":", 1)[1].strip())
    except Exception:
        raise SystemExit(f"Unexpected primesieve output: {out_line!r}")

    repo = _repository_ref()
    commit = _git_commit_hash()
    ci = _ci_context()

    receipt_without_integrity = {
        "receipt_metadata": {
            "schema_version": "1.1.0",
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "repository": repo,
            "commit_hash": commit,
            "workflow": ci["workflow"],
            "run_id": ci["run_id"],
            "actor": ci["actor"],
        },
        "environment": _environment_block(),
        "execution": {
            "tool": "primesieve",
            "mode": "-c2",
            "command": f"primesieve -c2 1 {N}",
            "args": {"n": N},
            "wall_time_seconds": wall_time,
        },
        "results": {
            "n": N,
            "twin_prime_count": twin_count,
            "unit": "pairs",
        },
    }

    digest = _canonical_sha256(receipt_without_integrity)
    receipt = dict(receipt_without_integrity)
    receipt["integrity"] = {"method": "sha256", "digest": digest}

    json_path = pathlib.Path(f"results/primesieve_twin_count_{N}.json")
    json_path.write_text(json.dumps(receipt, indent=2) + "\n")

    # Companion file: sha256 of the full JSON file on disk
    sha = _sh(["sha256sum", str(json_path)]).strip()
    sha_path = pathlib.Path(f"results/primesieve_twin_count_{N}.sha256")
    sha_path.write_text(sha + "\n")

    print("WROTE:", json_path)
    print("SHA256:", sha)


if __name__ == "__main__":
    main()
