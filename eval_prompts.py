import argparse
import hashlib
import json
import sys
from pathlib import Path

from check_prompt_pin import ROOT, validate
from prompt_app import predict


def evaluate(prompt_path=None, responses=None, golden=ROOT / "evals/golden.jsonl"):
    config, pin = validate()
    path = prompt_path or ROOT / "prompts" / pin["file"]
    prompt = json.loads(path.read_text())
    rows = [json.loads(line) for line in golden.read_text().splitlines()]
    if not rows or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Empty or duplicate golden dataset")
    if json.loads((ROOT / "fixtures/quarantine.json").read_text()):
        raise ValueError("Quarantine requires human review; denominator cannot shrink")
    if any(r["urgency"] not in {"high", "low"} for r in rows):
        raise ValueError("Invalid golden label")
    outputs = json.loads(responses.read_text()) if responses else {
        r["id"]: predict(r["message"], prompt) for r in rows}
    if set(outputs) != {r["id"] for r in rows} or any(
            value not in {"high", "low"} for value in outputs.values()):
        raise ValueError("Missing, unexpected, or invalid outputs")
    correct = sum(outputs[r["id"]] == r["urgency"] for r in rows)
    metric = correct / len(rows)
    return {"status": "PASS" if metric >= config["eval_threshold"] else "FAIL",
            "urgency_agreement": metric, "threshold": config["eval_threshold"],
            "correct": correct, "total": len(rows), "prompt_version": prompt["version"],
            "prompt_sha": hashlib.sha256(path.read_bytes()).hexdigest(),
            "provider": "recorded-fixture" if responses else "deterministic-stub"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=Path)
    parser.add_argument("--responses", type=Path)
    args = parser.parse_args()
    try:
        report = evaluate(args.prompt, args.responses)
        print(json.dumps(report))
        sys.exit(0 if report["status"] == "PASS" else 1)
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}))
        sys.exit(1)
