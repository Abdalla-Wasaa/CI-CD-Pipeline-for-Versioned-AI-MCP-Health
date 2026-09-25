# Week 8 Capstone: CI/CD for Versioned AI + MCP Health

## Overview
A standalone LLMOps release simulation for AfyaPlus: versioned prompts and configuration,
a FastAPI application, a versioned MCP server, fail-closed release gates, container builds,
and a reversible deployment stub. No training, external LLM call, real patient data,
or cloud account is required. This is educational software, not a clinical decision system.

## Quick start
Run from this repository root with Python 3.12 and Docker:
```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.lock
python check_prompt_pin.py
pytest -q
python eval_prompts.py
python scripts/check_mcp_health.py
uvicorn prompt_app:app --host 127.0.0.1 --port 8000
# In another terminal: curl http://127.0.0.1:8000/health
```
Full local pipeline (Docker daemon required):
```sh
python scripts/pipeline.py
```
The `/triage` endpoint accepts `{"patient_message":"chest pain today"}` and returns
an urgency label, simulation flag and trace ID. It uses deterministic rules extracted
from the selected prompt; it does not claim to measure real LLM or clinical quality.
The unauthenticated demo binds locally by default. Add validated authentication,
rate limiting, TLS, and clinical review before exposing it beyond a local demo.

## Version alignment strategy
The current stable release train is **1.2.0**. App, configuration, prompt and MCP versions
all match `config/triage.yaml` and `prompts/pin.json`. The intended release tag is
`v1.2.0`; CI image tags are `afyaplus:1.2.0-<full-git-sha>` (local runner uses 12 SHA
characters). The SHA suffix identifies the exact build and avoids overwriting another
build of the same release. Git tags are made only after release review. Candidates
are not release tags. Health reports all component versions plus prompt SHA-256.
A rollback restores the whole previous image, including its prompt, configuration
and MCP files; never edit a running image or repoint a prompt independently.

## Prompt versioning
`prompts/triage_system_v1.2.0.txt` contains the stable JSON-encoded system prompt and
simulation rules. `1.3.0-candidate` is an intentionally regressing proposal, not active.
`check_prompt_pin.py` rejects invalid stable semver, filenames, hashes, content versions,
and component mismatch. To release a change, create a new prompt file, update all
manifest versions and the pin hash, evaluate it, obtain review, then tag the merge.
Do not edit a released prompt in place. Threshold changes require a separately reviewed
policy change; the gate enforces the approved 0.85 threshold.

## MCP versioning and health
`logistics_mcp_versioned.py` reports release version in MCP `serverInfo`, exposes
`check_stock`, and serves `clinics://directory` with synthetic data. The health gate
starts the local stdio server, initializes an actual MCP session, checks protocol
handshake and server version, lists required tools/resources, reads the directory,
and invokes the stock tool. Errors, disconnects and the 20-second timeout return 1.

The local fallback is the same MCP implementation with synthetic storage, not a
constant success response. To inspect a deployed MCP service through the same checks:
```sh
python scripts/check_mcp_health.py --url http://127.0.0.1:8000/mcp
# Start the standalone MCP HTTP demo in a separate terminal first:
MCP_TRANSPORT=streamable-http python logistics_mcp_versioned.py
```
Do not run the FastAPI and MCP HTTP processes on the same port simultaneously.
Authenticated production transport requires a separately configured client adapter.
SDK reference: https://github.com/modelcontextprotocol/python-sdk/tree/v1.x

## Pipeline architecture
Both `.github/workflows/ci.yml` and `azure-pipelines.yml` implement:
```text
lint + pin → tests → eval → mcp_health → Docker build → deploy stub
```
Each stage depends on success of its predecessor. No continue-on-error or unconditional
deployment exists. PRs validate and build; only `main` may deploy. GitHub supports PR,
push to main and manual `workflow_dispatch`; Azure supports PR/push for GitHub sources
and manual Run pipeline. On Azure Repos, configure PR build validation as a branch policy.
Build artifacts carry the exact Docker image to deployment. The deploy stage verifies
its pin and records the image in `artifacts/deployment.json`; it does not run a cloud
workload. CI uploads the deployment record. Configure `capstone-stub` environment
reviewers if an approval demonstration is required; YAML alone cannot enforce reviewers.
Live deployment must introduce a protected production environment, external state,
registry digest pinning, secrets management and smoke checks before traffic switching.

## Eval gate
`evals/golden.jsonl` contains 10 synthetic cases. **urgency_agreement** is exact urgency
matches divided by **all 10 cases**, with a required score **>= 0.85**. Thus 9/10 passes;
8/10 fails. Predictions are freshly generated from prompt rules by default, rather
than grading a passing fixture. `--responses` supports a recorded-output negative test.
The candidate loses emergency terms and scores 0.50; the all-low fixture scores 0.40.
Empty/duplicate datasets, malformed or missing outputs, invalid labels, pin errors,
or any nonempty quarantine fail closed. Quarantine cannot silently reduce the denominator.
The small set proves release mechanics only; it cannot establish clinical safety.
```sh
python eval_prompts.py --prompt prompts/triage_system_v1.3.0-candidate.txt
python eval_prompts.py --responses fixtures/responses/failing.json
# Both commands must return exit code 1.
python scripts/pipeline.py --prompt prompts/triage_system_v1.3.0-candidate.txt --state artifacts/blocked-eval.json
python scripts/pipeline.py --mcp-server /nonexistent/server.py --state artifacts/blocked-mcp.json
# Both fail before build/deploy, and neither state file is created.
```
See [recorded verification](docs/verification.md) and [gate output](docs/gate-evidence.txt).

## Fallback declaration
- **workflow_dispatch:** GitHub Actions → Versioned AI release → Run workflow on main.
- **act:** `act pull_request -W .github/workflows/ci.yml` runs validation locally with
  Docker. Artifact actions may need act's artifact server (`--artifact-server-path /tmp/act-artifacts`).
  Hosted Actions is authoritative; act parity is not claimed without a local run.
- **Stub retrain job:** `python scripts/retrain_stub.py` explicitly reports skipped
  training. Retraining is outside this LLMOps task and is not a deployment prerequisite.
- **Local MCP health stub:** real stdio protocol, synthetic clinic storage, same checks
  as the remote transport. There is no automatic success fallback if remote health fails.
- **No GPU:** all evaluation is CPU-only deterministic simulation.
- **No cloud:** Docker build plus deploy-state record; no claim of serving live traffic.

## Coursework reuse
**Week 6:** inspected `wk6/afyaplus-platform/monday/secure_triage_api.py` and
`thursday/logistics_mcp.py`. Reused the architecture of FastAPI validation, versioned
health, MCP tools, and a clinic directory resource. Implementations are independent;
no credentials, auth defaults, clinic records, or coursework files were copied.
Authentication patterns are documented for future production integration.

**Week 7:** inspected `wk7/tuesday/triage_api.py` and `thursday/quality_smoke.json`.
Adapted the deterministic urgency stand-in and agreement-based quality gate; moved
rule selection into versioned prompts and made regression fail the release process.
All Week 6 and Week 7 files remain unchanged.

## Operations and governance
Read [runbook](runbook.md), [clinical operations brief](clinical_ops_change_brief.md),
[contribution rules](CONTRIBUTING.md), and [changelog](CHANGELOG.md).
**Recommend:** engineering presents version, metrics and health evidence.
**Against:** clinical operations and security reviewers identify concerns and can block.
**Decide:** the accountable release owner approves or rejects the release after review.
The pipeline cannot supply human approval or replace clinical judgment.

## Definition of Done
- [x] Tests pass; integrity and regression failures are covered.
- [x] Stable eval meets threshold; candidate regression fails closed.
- [x] MCP protocol, tools, resources and version checked; failure blocks deployment.
- [x] Deployment-state rollback tested.
- [x] Documentation, Docker artifacts and both pipeline YAML files included.
- [ ] Human release approval completed (not fabricated by automation).
- [ ] Production readiness review completed (outside this local simulation).
See verification for the exact tests and execution limitations.
