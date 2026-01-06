#!/usr/bin/env python3
"""
Physics TruthBomb v1 validator
- Validates required dual-notation structure (as_above / so_below)
- Computes SHA-256 for the declared physics PDF
- Writes/overwrites uhd/receipts/physics/checksums.latest.txt
- Appends uhd/receipts/physics/checksums.ledger.txt lines:
  <sha256>  <path>  <utc_iso8601>

Stdlib only; no network access.
"""

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
from typing import Any, Dict, List

ALLOWED_PATH = "uhd/imports/physics/Halliday_Cheatsheet.pdf"
LATEST_FILE = "uhd/receipts/physics/checksums.latest.txt"
LEDGER_FILE = "uhd/receipts/physics/checksums.ledger.txt"


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _is_str_list(x: Any) -> bool:
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def _validate_as_above(node: Dict[str, Any]) -> None:
    req = [
        "version",
        "purpose",
        "nonnegotiables",
        "inputs",
        "outputs",
        "procedure_steps",
        "stop_conditions",
        "receipt_requirements",
    ]
    _require(isinstance(node, dict), "as_above must be object")
    for k in req:
        _require(k in node, f"as_above missing required key: {k}")

    _require(node["version"] == "1.0.0", "as_above.version must be '1.0.0'")
    _require(isinstance(node["purpose"], str), "as_above.purpose must be string")
    _require(_is_str_list(node["nonnegotiables"]), "as_above.nonnegotiables must be [string]")

    inputs = node["inputs"]
    _require(isinstance(inputs, dict), "as_above.inputs must be object")
    _require("artifacts" in inputs and "parameters" in inputs, "as_above.inputs missing artifacts/parameters")
    arts = inputs["artifacts"]
    _require(isinstance(arts, list) and len(arts) == 1, "as_above.inputs.artifacts must be a single-item array")
    art = arts[0]
    _require(isinstance(art, dict), "artifact must be object")
    _require(art.get("path") == ALLOWED_PATH, f"artifact.path must be {ALLOWED_PATH}")

    params = inputs["parameters"]
    _require(isinstance(params, dict), "as_above.inputs.parameters must be object")
    _require(params.get("hash_algorithm") == "sha256", "hash_algorithm must be 'sha256'")

    outputs = node["outputs"]
    _require(isinstance(outputs, dict), "as_above.outputs must be object")
    _require("receipts" in outputs and isinstance(outputs["receipts"], list), "as_above.outputs.receipts must be [string]")
    _require(
        set(outputs["receipts"]) == {LATEST_FILE, LEDGER_FILE},
        "outputs.receipts must contain latest and ledger files",
    )

    _require(_is_str_list(node["procedure_steps"]), "as_above.procedure_steps must be [string]")

    sc = node["stop_conditions"]
    _require(isinstance(sc, dict), "as_above.stop_conditions must be object")
    _require(sc.get("on_missing_artifact") == "stop", "on_missing_artifact must be 'stop'")
    _require(sc.get("on_invalid_structure") == "stop", "on_invalid_structure must be 'stop'")

    rr = node["receipt_requirements"]
    _require(isinstance(rr, dict), "as_above.receipt_requirements must be object")
    _require(rr.get("latest_file") == LATEST_FILE, "receipt_requirements.latest_file mismatch")
    _require(rr.get("ledger_file") == LEDGER_FILE, "receipt_requirements.ledger_file mismatch")
    _require(isinstance(rr.get("format"), str) and rr.get("format"), "receipt_requirements.format must be non-empty string")


def _validate_so_below(node: Dict[str, Any]) -> None:
    req = [
        "version",
        "purpose_human",
        "ux_notes",
        "inputs_friendly",
        "outputs_friendly",
        "success_criteria",
    ]
    _require(isinstance(node, dict), "so_below must be object")
    for k in req:
        _require(k in node, f"so_below missing required key: {k}")
    _require(node.get("version") == "v1", "so_below.version must be 'v1'")
    _require(isinstance(node.get("purpose_human"), str), "so_below.purpose_human must be string")
    _require(_is_str_list(node.get("ux_notes")), "so_below.ux_notes must be [string]")

    inf = node["inputs_friendly"]
    _require(isinstance(inf, dict), "inputs_friendly must be object")
    _require(inf.get("artifact") == "Halliday_Cheatsheet.pdf", "inputs_friendly.artifact must be 'Halliday_Cheatsheet.pdf'")
    p = inf.get("parameters")
    _require(isinstance(p, dict) and p.get("hash") == "sha256", "inputs_friendly.parameters.hash must be 'sha256'")

    _require(isinstance(node.get("outputs_friendly"), str), "outputs_friendly must be string")
    _require(_is_str_list(node.get("success_criteria")), "success_criteria must be [string]")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_latest(path: str, line: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(line + "\n")


def append_ledger(path: str, line: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Physics TruthBomb v1 validator")
    parser.add_argument(
        "--spec",
        default="uhd/spec/physics/Physics_Corpus_Spec_v1.json",
        help="Path to physics spec JSON",
    )
    args = parser.parse_args(argv)

    spec = _load_json(args.spec)
    _require(isinstance(spec, dict), "spec root must be object")
    _require("as_above" in spec and "so_below" in spec, "spec must have 'as_above' and 'so_below'")
    _validate_as_above(spec["as_above"])  # raises on failure
    _validate_so_below(spec["so_below"])  # raises on failure

    art_path = spec["as_above"]["inputs"]["artifacts"][0]["path"]
    if not os.path.exists(art_path):
        raise FileNotFoundError(f"Artifact not found: {art_path}")

    sha_hex = sha256_file(art_path)
    ts = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    line = f"{sha_hex}  {art_path}  {ts}"

    write_latest(LATEST_FILE, line)
    append_ledger(LEDGER_FILE, line)

    print(f"Latest: {LATEST_FILE}\nLedger: {LEDGER_FILE}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
