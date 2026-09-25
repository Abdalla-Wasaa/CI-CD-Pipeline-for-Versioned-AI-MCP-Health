# Contributing

Branch from main using `feat/versioning`, `feat/eval-gate`, `feat/mcp-health`,
`feat/pipeline`, `docs/runbook`, or a similarly scoped name. Use semantic commits such
as `feat(eval): add fail-closed urgency gate` and `docs(runbook): document rollback`.
Keep work inside this standalone repository; never modify coursework as part of it.

Use semver: major for breaking contracts, minor for compatible features, patch for
fixes. Release train versions match app, config, prompt and MCP. Create a new prompt
file and pin digest; never mutate historical released content. Tag approved main
merges `vX.Y.Z`. CI tags images with version and source SHA.

PRs must explain the behavior change, reference evaluation/MCP evidence, include
meaningful tests and updated runbooks, and disclose fallback modes. Require a human
reviewer and green checks before merge. Reviewers inspect prompt diffs, golden dataset
changes, quarantine entries, dependency changes and rollback compatibility. Release
owner records approval separately from implementation completion. Protect main and
configure required checks in GitHub settings; neither is claimed to be enforced by
this text alone. Do not bypass branch policies.

Never commit `.env`, `.claude/`, `CLAUDE.md`, `AGENTS.md`, credentials, tokens or secrets.
Inspect staged files before committing. Use ignored local environment files and
provider secret stores; never put secrets in PR descriptions or logs.

Definition of Done: tests pass, eval >= 0.85, MCP health passes, rollback tested,
documentation updated, and human approval completed. An unchecked approval is an
explicit open release requirement, not permission for automation to invent a sign-off.
