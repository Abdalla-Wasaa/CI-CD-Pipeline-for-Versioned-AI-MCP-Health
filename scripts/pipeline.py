"""Local pipeline; failed subprocesses stop execution before deployment."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from check_prompt_pin import validate  # noqa: E402


def run(command):
    print("RUN " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt")
    parser.add_argument("--mcp-server")
    parser.add_argument("--state", default="artifacts/deployment.json")
    args = parser.parse_args()
    py = sys.executable
    run([py, "-m", "ruff", "check", "."])
    run([py, "check_prompt_pin.py"])
    run([py, "-m", "pytest", "-q"])
    run([py, "eval_prompts.py"] + (["--prompt", args.prompt] if args.prompt else []))
    run([py, "scripts/check_mcp_health.py"] + (
        ["--server", args.mcp_server] if args.mcp_server else []))
    version = validate()[1]["version"]
    sha = subprocess.check_output(["git", "rev-parse", "--short=12", "HEAD"], cwd=ROOT,
                                  text=True).strip()
    image = f"afyaplus:{version}-{sha}"
    run(["docker", "build", "-t", image, "."])
    run([py, "scripts/deploy_stub.py", "--image", image, "--state", args.state])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"BLOCKED: deployment not reached: {exc}", flush=True)
        sys.exit(1)
