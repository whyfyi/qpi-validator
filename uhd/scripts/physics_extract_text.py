#!/usr/bin/env python3
"""
Physics Corpus Text Extractor v1
- Input PDF: --pdf uhd/imports/physics/Halliday_Cheatsheet.pdf
- Output TXT: uhd/receipts/physics/halliday_cheatsheet.latest.txt
- Uses 'pdftotext' if installed (via subprocess). If missing, exits with a
  clear message describing installation (e.g., poppler-utils or xpdf tools).
- After extraction, computes sha256 of BOTH the PDF and the extracted TXT and
  writes:
    - Overwrite: uhd/receipts/physics/extract.latest.txt
    - Append:    uhd/receipts/physics/extract.ledger.txt
  Lines use format:
    <sha256>  <path>  <utc_iso8601>

Stdlib + subprocess only. No network access.
"""

import argparse
import datetime as _dt
import hashlib
import os
import subprocess
import sys
from typing import List

DEFAULT_PDF = "uhd/imports/physics/Halliday_Cheatsheet.pdf"
TXT_OUT = "uhd/receipts/physics/halliday_cheatsheet.latest.txt"
LATEST = "uhd/receipts/physics/extract.latest.txt"
LEDGER = "uhd/receipts/physics/extract.ledger.txt"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_pdftotext() -> str:
    """Return path to 'pdftotext', or raise with helpful install guidance."""
    from shutil import which

    exe = which("pdftotext")
    if exe:
        return exe
    msg = (
        "pdftotext not found. Install Poppler's pdftotext utility.\n"
        "Examples:\n"
        "- Debian/Ubuntu: sudo apt-get install poppler-utils\n"
        "- macOS (Homebrew): brew install poppler\n"
        "- Windows (choco): choco install poppler\n"
        "Alternatively install Xpdf tools providing pdftotext."
    )
    raise SystemExit(msg)


def extract_with_pdftotext(pdftotext: str, pdf: str, txt_out: str) -> None:
    os.makedirs(os.path.dirname(txt_out), exist_ok=True)
    # 'pdftotext <pdf> <txt>' keeps layout reasonably with -layout
    cmd = [pdftotext, "-layout", pdf, txt_out]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except FileNotFoundError:
        # Should not happen due to ensure_pdftotext(), but guard anyway
        raise SystemExit("pdftotext executable disappeared before running")
    if res.returncode != 0:
        raise SystemExit(f"pdftotext failed (code {res.returncode}): {res.stderr.decode('utf-8', 'replace')}")


def write_latest(path: str, lines: List[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def append_ledger(path: str, lines: List[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Physics PDF -> text extractor")
    parser.add_argument("--pdf", default=DEFAULT_PDF, help="Path to Halliday PDF inside repo")
    args = parser.parse_args(argv)

    pdf = args.pdf
    if not os.path.exists(pdf):
        raise SystemExit(f"PDF not found: {pdf}")

    pdftotext = ensure_pdftotext()
    extract_with_pdftotext(pdftotext, pdf, TXT_OUT)

    ts = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    sha_pdf = sha256_file(pdf)
    sha_txt = sha256_file(TXT_OUT)

    lines = [
        f"{sha_pdf}  {pdf}  {ts}",
        f"{sha_txt}  {TXT_OUT}  {ts}",
    ]

    write_latest(LATEST, lines)
    append_ledger(LEDGER, lines)

    print(f"Text written: {TXT_OUT}\nLatest: {LATEST}\nLedger: {LEDGER}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit as e:
        # Forward message and exit code if provided, else generic code 2
        msg = str(e)
        if msg:
            print(msg, file=sys.stderr)
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
