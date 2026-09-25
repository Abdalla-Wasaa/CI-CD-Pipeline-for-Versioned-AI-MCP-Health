# Deployment and incident runbook

## Scope and approval
This runbook operates a synthetic release simulation. The GitHub/Azure deploy stage
records a verified image identifier; it is not a cloud deployment. Release owner,
clinical operations lead, and engineering reviewer are roles awaiting named human
assignment. Record their decisions in the release PR. Configure protected main,
required CI checks, and environment reviewers in repository settings before live use.
Never mark approval complete solely because CI is green.

## Release procedure
1. Create `feat/<scope>` or `fix/<scope>` from main. Add a semver prompt file and update
   config/pin together. Breaking interfaces use major; compatible capabilities minor;
   corrections patch. Candidate filenames use a prerelease suffix and are not active.
2. Run `python check_prompt_pin.py`, `pytest -q`, `python eval_prompts.py`, and
   `python scripts/check_mcp_health.py`; attach scores and MCP metadata to the PR.
3. Run `python scripts/pipeline.py` to build Docker and record the local stub release.
4. Review changes, regression evidence and clinical brief. Human release owner decides.
5. Merge only after required checks pass. Main CI builds the exact commit image,
   transfers it to deploy, validates the pin, and uploads the deployment record.
6. Following approval, tag that merge as `v<version>` and retain the image and record.
   Git tags alone do not trigger this workflow; main push or manual dispatch does.
7. For a live system, deploy by registry digest to staging, verify `/health`, eval and
   live MCP health, then require environment approval before switching traffic.

## Rollback procedure and rehearsal
For local state simulation:
```sh
python scripts/deploy_stub.py --image afyaplus:1.2.0-known-good
python scripts/deploy_stub.py --image afyaplus:1.3.0-candidate
python scripts/deploy_stub.py --rollback
cat artifacts/deployment.json
```
The current image must be `afyaplus:1.2.0-known-good`. The unit test repeats this
with isolated state. A rollback without a previous image fails. CI runners are
fresh, so download prior deployment records to reconstruct history; the demonstration
does not pretend to persist cross-run state automatically.

For an actual incident, stop promotion, identify the previous approved registry digest
from the deployment ledger, deploy that whole image, and check `/health` versions,
prompt hash, MCP health and smoke traffic before switching back. Restore app, prompt,
config and MCP together. Retain the failing image and trace evidence. Do not rebuild
an old release from changed dependencies. Reverting a commit alone does not restore
already running containers. External data/schema rollback needs a separate reviewed plan.

## Logs and trace discovery
- GitHub Actions job logs: lint, tests, eval, mcp_health, build, deploy. Artifacts:
  `release-image` (7 days), `deployment-record` (repository retention default).
- Azure pipeline stage logs; `release` and `deployment-record` artifacts.
- Local console output and `artifacts/deployment.json`; committed sample gate output
  lives in `docs/gate-evidence.txt`.
- `/triage` returns a generated UUID trace ID. Search application stdout/container logs
  for that UUID (`docker logs <container>`). Match prompt version from its JSON event
  to the image record and `/health` metadata, then to the PR and commit.
- Patient message text and credentials are not logged by the app. There is no distributed
  tracing backend in this demo; connect an approved backend before production use.

## Incident response
Engineering on-call freezes releases and collects failing stage, commit, image, version,
trace IDs and timestamps. Clinical operations assesses service impact and decides
whether to suspend automated assistance. The release owner authorizes rollback or
recovery. Any health failure or eval below 0.85 is No-Go; never lower the threshold
as an incident workaround. Escalate patient-safety concerns immediately to clinical
leadership. After recovery, add a regression case, document root cause and obtain review.

## Governance
Recommend: engineering provides evidence. Against: clinical/security reviewers record
objections and hold release. Decide: release owner records a human Go/No-Go decision.
Automation implements that decision; it cannot approve itself.
