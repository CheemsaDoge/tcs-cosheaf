# Operator Runbook

This is the v1.0 operator entry point for humans and external AI operators.
The CLI is the oracle. Skills and MCP docs are optional guidance only.

For the longer historical runbook, see
[Codex Operator Runbook](CODEX_OPERATOR_RUNBOOK.md).

## One-Command Demo

Use the workspace template:

```bash
git clone https://github.com/CheemsaDoge/tcs-cosheaf-workspace-template.git
cd tcs-cosheaf-workspace-template
make ai-math-collaborator-demo
```

The demo writes ignored runtime output only. It does not promote artifacts,
write accepted knowledge, create human review, mutate public KB, require MCP,
or call hosted providers.

## Manual Loop

1. Inspect the workspace:

```bash
cosheaf workspace info
cosheaf validate
cosheaf gate run
```

2. Build context for one issue:

```bash
cosheaf context build <issue-id>
```

3. Start and run a bounded workflow:

```bash
cosheaf workflow start --issue <issue-id> --json
cosheaf workflow run <workflow-id> --max-steps 3 --execute-local-actions --json
cosheaf workflow readiness <workflow-id> --json
```

4. Check review context:

```bash
cosheaf workflow cross-check <workflow-id> --json
cosheaf workflow evidence-report <workflow-id> --json
cosheaf gap list <workflow-id> --json
cosheaf workflow handoff build <workflow-id> --json
cosheaf workflow handoff scan <handoff-id> --json
```

5. Run bounded campaign attempts when useful:

```bash
cosheaf campaign start --issue <issue-id> --json
cosheaf campaign next <campaign-id> --json
cosheaf campaign export-task <campaign-id> --out .cosheaf/tasks/operator_task.json --json
cosheaf campaign import-result <campaign-id> --input-json result.json --json
cosheaf campaign scan <campaign-id> --json
cosheaf campaign handoff <campaign-id> --out .cosheaf/campaign-handoff --json
```

6. Record sidecar memory and benchmark evidence:

```bash
cosheaf memory rebuild --json
cosheaf benchmark run --suite smoke --json
cosheaf report benchmark <run-id> --out .cosheaf/reports/benchmark --json
```

7. Re-run repository checks before opening a PR:

```bash
cosheaf validate
cosheaf gate run
```

## Operator Rules

- Keep public KB readonly in user workspaces.
- Keep private research under `kb/private`.
- Do not put private conjectures in public KB.
- Do not copy review-context runtime output into accepted KB.
- Do not describe skipped checks as passes.
- Do not claim Lean, SAT, SMT, verifier, or gate success unless the relevant
  checker actually ran and recorded that result.
- AI output is not human review.
- Promotion still requires the normal artifact lifecycle.

See [AI Math Collaborator MVP](AI_MATH_COLLABORATOR_MVP.md),
[Workflows](WORKFLOWS.md), [Campaigns](CAMPAIGNS.md),
[Checkers](CHECKERS.md), [Benchmarks](BENCHMARKS.md), and
[Authority Boundaries](AUTHORITY_BOUNDARIES.md).
