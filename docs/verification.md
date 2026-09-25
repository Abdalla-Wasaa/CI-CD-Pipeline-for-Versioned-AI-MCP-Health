# Verification evidence

Executed in the supplied workspace using Python 3.12 and a working Docker daemon.

| Check | Result |
| --- | --- |
| Ruff lint | Pass |
| Pytest | 12 passed; one upstream Starlette/AnyIO deprecation warning |
| Prompt pin and version validation | Pass |
| Stable urgency agreement | 1.00 (10/10), threshold 0.85 |
| Candidate agreement | 0.50, exit 1; pipeline blocked before Docker/deploy |
| Failing recorded response fixture | 0.40, exit 1 |
| Unavailable MCP | Exit 1; pipeline blocked before Docker/deploy |
| Real stdio MCP handshake, tool and resource access | Pass |
| Wrong version / missing tool / missing resource | Rejected in tests |
| Missing outputs / empty golden set / modified prompt | Rejected in tests |
| Rollback and absent previous release | Pass |
| GitHub and Azure YAML parse | Pass |
| Full local pipeline | Pass through Docker build and deployment-state record |
| Docker API health and in-container MCP health | Pass |

The local build used source commit `c54478549e92` plus the documentation then present
in the working directory. Hosted CI builds the committed source. Raw negative-gate
output is in [gate-evidence.txt](gate-evidence.txt). The positive local build log was
retained at `/tmp/week8-pipeline.log` on the authoring machine.

Azure hosted execution, act, a live cloud deployment, and clinical approval have not
been performed. The local rollback rehearses deployment records, not cloud traffic.
GitHub hosted CI results are visible on the implementation PR and repository Actions tab.
