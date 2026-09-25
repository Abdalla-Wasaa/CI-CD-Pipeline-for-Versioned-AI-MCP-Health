"""Local release-state simulation. No cloud resources are changed."""
import argparse
import json
import os
from pathlib import Path


def deploy(image, state):
    if not image or not (":" in image or "@sha256:" in image):
        raise ValueError("An explicit immutable image identifier is required")
    state.parent.mkdir(parents=True, exist_ok=True)
    old = json.loads(state.read_text()) if state.exists() else {"current": None}
    data = {"mode": "deployment-stub", "current": image, "previous": old["current"]}
    temporary = state.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(temporary, state)
    return data


def rollback(state):
    data = json.loads(state.read_text())
    if not data.get("previous"):
        raise ValueError("No previous release is available")
    return deploy(data["previous"], state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image")
    parser.add_argument("--rollback", action="store_true")
    parser.add_argument("--state", type=Path, default=Path("artifacts/deployment.json"))
    args = parser.parse_args()
    try:
        if args.rollback == bool(args.image):
            raise ValueError("Choose either --image or --rollback")
        print(json.dumps(rollback(args.state) if args.rollback else deploy(args.image, args.state)))
    except Exception as exc:
        print(f"FAIL deployment: {exc}")
        raise SystemExit(1)
