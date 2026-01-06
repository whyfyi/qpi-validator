#!/usr/bin/env python3
"""
Truth Bomb v2 validator
- Validates the required dual-notation structure (as_above / so_below)
- Computes SHA-256 for each declared artifact path
- Appends lines to uhd/receipts/truthbomb/checksums.txt as:
  <sha256>  <path>  <utc_iso8601>

No external dependencies; standard library only.
"""

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
from typing import Any, Dict, List


ALLOWED_ARTIFACT_PATHS = {
    "uhd/imports/WhyFYI_5G.json",
    "uhd/imports/WhyFYI5G.json",
    "uhd/imports/DivineAlgebra_Master.json",
    "uhd/imports/QuantumManifestationMatrix_Master.json",
    "uhd/imports/GPAI_Conversation_Update_v1_1_5_2026_TimeStamp.txt",
}


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _is_str_list(x: Any) -> bool:
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def _validate_as_above(node: Dict[str, Any]) -> None:
    req_keys = [
        "version",
        "purpose",
        "nonnegotiables",
        "inputs",
        "outputs",
        "procedure_steps",
        "stop_conditions",
        "receipt_requirements",
    ]
    _require(isinstance(node, dict), "as_above must be an object")
    for k in req_keys:
        _require(k in node, f"as_above missing required key: {k}")

    _require(node["version"] == "2.0.0", "as_above.version must be '2.0.0'")
    _require(isinstance(node["purpose"], str), "as_above.purpose must be string")
    _require(_is_str_list(node["nonnegotiables"]), "as_above.nonnegotiables must be [string]")

    inputs = node["inputs"]
    _require(isinstance(inputs, dict), "as_above.inputs must be object")
    _require("artifacts" in inputs and "parameters" in inputs, "as_above.inputs missing artifacts/parameters")
    artifacts = inputs["artifacts"]
    _require(isinstance(artifacts, list), "as_above.inputs.artifacts must be array")
    for idx, art in enumerate(artifacts):
        _require(isinstance(art, dict), f"artifact[{idx}] must be object")
        _require("path" in art, f"artifact[{idx}] missing path")
        p = art["path"]
        _require(isinstance(p, str), f"artifact[{idx}].path must be string")
        _require(p in ALLOWED_ARTIFACT_PATHS, f"artifact[{idx}].path not allowed: {p}")

    params = inputs["parameters"]
    _require(isinstance(params, dict), "as_above.inputs.parameters must be object")
    _require(params.get("hash_algorithm") == "sha256", "as_above.inputs.parameters.hash_algorithm must be 'sha256'")

    outputs = node["outputs"]
    _require(isinstance(outputs, dict), "as_above.outputs must be object")
    _require("receipts" in outputs and isinstance(outputs["receipts"], list), "as_above.outputs.receipts must be [string]")
    _require(outputs["receipts"] == ["uhd/receipts/truthbomb/checksums.txt"], "as_above.outputs.receipts must contain the checksums file")

    _require(_is_str_list(node["procedure_steps"]), "as_above.procedure_steps must be [string]")

    sc = node["stop_conditions"]
    _require(isinstance(sc, dict), "as_above.stop_conditions must be object")
    _require(sc.get("on_missing_artifact") == "stop", "as_above.stop_conditions.on_missing_artifact must be 'stop'")
    _require(sc.get("on_invalid_structure") == "stop", "as_above.stop_conditions.on_invalid_structure must be 'stop'")

    rr = node["receipt_requirements"]
    _require(isinstance(rr, dict), "as_above.receipt_requirements must be object")
    _require(rr.get("file") == "uhd/receipts/truthbomb/checksums.txt", "as_above.receipt_requirements.file must be checksums.txt")
    _require(isinstance(rr.get("format"), str) and rr.get("format"), "as_above.receipt_requirements.format must be non-empty string")


def _validate_so_below(node: Dict[str, Any]) -> None:
    req_keys = [
        "version",
        "purpose_human",
        "ux_notes",
        "inputs_friendly",
        "outputs_friendly",
        "success_criteria",
    ]
    _require(isinstance(node, dict), "so_below must be an object")
    for k in req_keys:
        _require(k in node, f"so_below missing required key: {k}")
    _require(node["version"] == "v2", "so_below.version must be 'v2'")
    _require(isinstance(node["purpose_human"], str), "so_below.purpose_human must be string")
    _require(_is_str_list(node["ux_notes"]), "so_below.ux_notes must be [string]")

    inf = node["inputs_friendly"]
    _require(isinstance(inf, dict), "so_below.inputs_friendly must be object")
    _require("artifacts" in inf and "parameters" in inf, "so_below.inputs_friendly missing artifacts/parameters")
    _require(_is_str_list(inf["artifacts"]), "so_below.inputs_friendly.artifacts must be [string]")
    allowed_names = {
        "WhyFYI_5G.json",
        "WhyFYI5G.json",
        "DivineAlgebra_Master.json",
        "QuantumManifestationMatrix_Master.json",
        "GPAI_Conversation_Update_v1_1_5_2026_TimeStamp.txt",
    }
    for idx, name in enumerate(inf["artifacts"]):
        _require(name in allowed_names, f"so_below.inputs_friendly.artifacts[{idx}] not allowed: {name}")
    p = inf["parameters"]
    _require(isinstance(p, dict), "so_below.inputs_friendly.parameters must be object")
    _require(p.get("hash") == "sha256", "so_below.inputs_friendly.parameters.hash must be 'sha256'")

    _require(isinstance(node["outputs_friendly"], str), "so_below.outputs_friendly must be string")
    _require(_is_str_list(node["success_criteria"]), "so_below.success_criteria must be [string]")


def validate_spec(spec: Dict[str, Any]) -> None:
    _require(isinstance(spec, dict), "Spec must be a JSON object")
    _require("as_above" in spec and "so_below" in spec, "Spec must have 'as_above' and 'so_below'")
    _validate_as_above(spec["as_above"])  # raises on failure
    _validate_so_below(spec["so_below"])  # raises on failure


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def append_receipt_line(receipts_path: str, sha_hex: str, artifact_path: str) -> None:
    ts = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    os.makedirs(os.path.dirname(receipts_path), exist_ok=True)
    with open(receipts_path, "a", encoding="utf-8") as f:
        f.write(f"{sha_hex}  {artifact_path}  {ts}\n")


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Truth Bomb v2 validator")
    parser.add_argument(
        "--spec",
        default="uhd/spec/truthbomb/TruthBomb_Spec_v2.json",
        help="Path to TruthBomb v2 spec JSON",
    )
    args = parser.parse_args(argv)

    spec = _load_json(args.spec)
    validate_spec(spec)

    as_above = spec["as_above"]
    artifacts = as_above["inputs"]["artifacts"]
    receipts_list = as_above["outputs"]["receipts"]
    receipts_path = receipts_list[0]

    for art in artifacts:
        path = art["path"]
        if not os.path.exists(path):
            raise FileNotFoundError(f"Artifact not found: {path}")
        sha_hex = sha256_file(path)
        append_receipt_line(receipts_path, sha_hex, path)

    # Minimal confirmation to stdout (no external commands)
    print(f"Wrote receipts to: {receipts_path}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
