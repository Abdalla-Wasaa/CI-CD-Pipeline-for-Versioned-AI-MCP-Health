import asyncio
import json
import shutil
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from check_prompt_pin import ROOT, validate
from eval_prompts import evaluate
from prompt_app import app
from scripts.check_mcp_health import check
from scripts.deploy_stub import deploy, rollback


def test_health_and_trace():
    client = TestClient(app)
    health = client.get("/health").json()
    assert health["app_version"] == health["prompt_version"] == health["mcp_version"]
    assert len(health["prompt_sha"]) == 64
    response = client.post("/triage", json={"patient_message": "chest pain today"})
    assert response.json()["urgency"] == "high"
    assert response.json()["trace_id"]
    assert client.post("/triage", json={"patient_message": ""}).status_code == 422


def test_pin_detects_tampering(tmp_path):
    for folder in ["prompts", "config"]:
        shutil.copytree(ROOT / folder, tmp_path / folder)
    prompt = tmp_path / "prompts/triage_system_v1.2.0.txt"
    prompt.write_text(prompt.read_text() + " ")
    with pytest.raises(ValueError, match="SHA"):
        validate(tmp_path)


def test_regression_and_missing_outputs(tmp_path):
    assert evaluate()["urgency_agreement"] == 1.0
    assert evaluate(ROOT / "prompts/triage_system_v1.3.0-candidate.txt")["status"] == "FAIL"
    assert evaluate(responses=ROOT / "fixtures/responses/failing.json")["status"] == "FAIL"
    missing = tmp_path / "missing.json"
    missing.write_text("{}")
    with pytest.raises(ValueError, match="outputs"):
        evaluate(responses=missing)


def test_empty_dataset(tmp_path):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    with pytest.raises(ValueError, match="Empty"):
        evaluate(golden=empty)


def test_eval_cli_fails_closed():
    result = subprocess.run([sys.executable, "eval_prompts.py", "--responses",
                             "fixtures/responses/failing.json"], cwd=ROOT, capture_output=True)
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "FAIL"


def test_mcp_handshake_tools_resource():
    assert asyncio.run(check())["status"] == "PASS"


def test_unavailable_mcp(tmp_path):
    with pytest.raises(Exception):
        asyncio.run(check(server=tmp_path / "absent.py"))


@pytest.mark.parametrize("fault", ["version", "tool", "resource"])
def test_broken_mcp_contract(tmp_path, fault):
    source = (ROOT / "logistics_mcp_versioned.py").read_text()
    source = "import sys\nsys.path.insert(0, " + repr(str(ROOT)) + ")\n" + source
    if fault == "version":
        source = source.replace("version = VERSION", 'version = "9.9.9"')
    elif fault == "tool":
        source = source.replace("@mcp.tool()", "")
    else:
        source = source.replace("clinics://directory", "clinics://missing")
    server = tmp_path / "broken.py"
    server.write_text(source)
    with pytest.raises(Exception):
        asyncio.run(check(server=server))


def test_rollback(tmp_path):
    state = tmp_path / "release.json"
    deploy("afyaplus:1.2.0-old", state)
    deploy("afyaplus:1.3.0-new", state)
    assert rollback(state)["current"] == "afyaplus:1.2.0-old"
    assert json.loads(state.read_text())["previous"] == "afyaplus:1.3.0-new"


def test_no_rollback_without_previous(tmp_path):
    state = tmp_path / "release.json"
    deploy("afyaplus:1.2.0-only", state)
    with pytest.raises(ValueError, match="previous"):
        rollback(state)
