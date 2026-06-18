# AI Math Collaborator MVP

The v1.0.0 AI Math Collaborator MVP packages the existing Cosheaf research
harness into a safe CLI-first workflow. It helps a human or external AI
operator gather context, plan bounded attempts, record failures and evidence,
produce draft/review-context output, and compare results against deterministic
benchmarks.

It is not an autonomous mathematician, theorem prover, Lean autoformalizer,
human reviewer, hosted-agent service, or accepted-knowledge authority.

## Canonical Demo

Start from the workspace template, not this framework repository:

```bash
git clone https://github.com/CheemsaDoge/tcs-cosheaf-workspace-template.git
cd tcs-cosheaf-workspace-template
make ai-math-collaborator-demo
```

The demo uses a readonly public KB root and a writable private draft overlay.
It runs workspace checks, context build, CLI-agent, strategy, research-run,
campaign, and benchmark/report paths. Runtime output stays under ignored
`.cosheaf/` paths and `context/TASKS/`.

The demo must not require hosted LLMs, secrets, MCP, accepted writes, human
review creation, public KB mutation, or artifact promotion.

## Framework CLI Shape

The stable v1.0 CLI surface is discoverable from the framework package:

```bash
cosheaf interface list --json
cosheaf workspace info
cosheaf validate
cosheaf gate run
cosheaf context build <issue-id>
cosheaf workflow start --issue <issue-id> --json
cosheaf workflow run <workflow-id> --max-steps 3 --execute-local-actions --json
cosheaf workflow cross-check <workflow-id> --json
cosheaf gap list <workflow-id> --json
cosheaf campaign start --issue <issue-id> --json
cosheaf campaign export-task <campaign-id> --out .cosheaf/tasks/operator_task.json --json
cosheaf campaign import-result <campaign-id> --input-json result.json --json
cosheaf memory rebuild --json
cosheaf benchmark run --suite smoke --json
cosheaf report benchmark <run-id> --out .cosheaf/reports/benchmark --json
```

Use `cosheaf research-run ...` for research-run provenance. `cosheaf run ...`
remains compatibility behavior for older scripts.

## Output Authority

Cosheaf outputs are separated by authority:

- artifacts under accepted KB paths require review, gates, and promotion;
- draft/proposal/runtime outputs are review context only;
- checker and verifier results are evidence records only when a real checker
  ran and recorded the result;
- skipped, unavailable, unsupported, and inconclusive rows are not passes;
- benchmark success is regression evidence, not proof or accepted status.

See [Authority Boundaries](AUTHORITY_BOUNDARIES.md),
[Security](SECURITY.md), and [Public/private policy](PUBLIC_PRIVATE_POLICY.md).
