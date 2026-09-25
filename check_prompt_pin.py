import hashlib
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
SEMVER = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"


def validate(root=ROOT):
    config = yaml.safe_load((root / "config/triage.yaml").read_text())
    pin = json.loads((root / "prompts/pin.json").read_text())
    version = pin["version"]
    if not re.fullmatch(SEMVER, version):
        raise ValueError("Release pin must use stable semver")
    if pin["file"] != f"triage_system_v{version}.txt":
        raise ValueError("Prompt filename/version mismatch")
    data = (root / "prompts" / pin["file"]).read_bytes()
    if hashlib.sha256(data).hexdigest() != pin["sha256"]:
        raise ValueError("Prompt SHA mismatch")
    if json.loads(data)["version"] != version:
        raise ValueError("Prompt content version mismatch")
    for key in ("app_version", "config_version", "mcp_version", "prompt_version"):
        if config[key] != version:
            raise ValueError(f"Version mismatch: {key}")
    if config["eval_threshold"] != 0.85:
        raise ValueError("Approved threshold must remain 0.85")
    return config, pin


if __name__ == "__main__":
    try:
        print(json.dumps({"status": "PASS", "version": validate()[1]["version"]}))
    except Exception as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)
