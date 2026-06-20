# Web Workbench Runbook

This runbook describes how to run the Web Workbench from a local checkout and
how to use it without weakening Cosheaf governance boundaries. The repository
remains the source of truth. Website output, server output, audit logs, gate
output, verifier output, GitHub PR state, and AI/operator text are workflow
context only.

## Modes

The Workbench has three operating modes:

- Static showcase mode: renders committed demo fixture data from
  `website/src/fixtures/site-data/`. It has no backend and cannot write
  repository files, call GitHub, store tokens, run providers, or inspect private
  repositories.
- Live local mode: reads the current repository through the localhost Cosheaf
  server. It can show live artifacts, issues, gates, audit records, PR status,
  and runtime metadata.
- Write-capable local mode: live local mode plus confirmed actions that route
  through `cosheaf.server`, `cosheaf.app`, storage services, and `cosheaf.forge`.
  Each write-class action must preview first, require explicit confirmation,
  run its policy checks, and append a redacted audit entry.

Hosted workspace mode is not production-ready. The current hosted auth surface
is a backend guard stub, not OAuth, a GitHub App login flow, sessions, cookies,
or a SaaS deployment.

## Local Setup

Use a feature branch or disposable fixture repository when testing write-capable
flows. Do not run local write actions from `main` unless the action is a
read-only preview or check.

From a fresh framework checkout:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m cosheaf.cli validate
python -m cosheaf.cli gate
```

For POSIX shells, activate the environment with:

```bash
source .venv/bin/activate
```

Install website dependencies separately:

```powershell
cd website
npm ci
npm test
npm run build
cd ..
```

Runtime outputs such as `.cosheaf/`, `context/TASKS/`, `website/dist/`, and
`website/.astro/` are local artifacts. Do not commit them unless a later task
explicitly changes that rule.

## Static Showcase

Static showcase mode is the safest public demo path. It uses committed fixture
JSON only:

```powershell
cd website
npm ci
npm test
npm run build
npm exec -- astro preview --host 127.0.0.1 --port 4321
```

Open:

```text
http://127.0.0.1:4321/
```

You can also inspect `website/dist/index.html` directly after the build. Static
mode is appropriate for public explanation and UI inspection. It is not the
interactive Workbench and cannot prove that a live repository is valid or ready
for promotion.

To refresh static demo fixture data, use only a demo-safe workspace and review
the diff before committing:

```powershell
python -m cosheaf.cli site export --demo --out website/src/fixtures/site-data
```

Before publishing, confirm the fixture contains no API keys, private research,
hidden reviewer identity, provider prompts, or non-demo accepted claims.

## Live Local Mode

Start the localhost server from the repository root:

```powershell
python -m cosheaf.cli server serve --readonly --port 8765 --local-actor "Ada Reviewer"
```

The server binds to `127.0.0.1`. Do not expose it on a public interface. The
`--local-actor` value is an audit label for the person at the keyboard; it is
not authentication, authorization, or cryptographic identity. Confirmed human
review and promotion actions are refused when no local actor is configured.

In another terminal, start Astro in explicit live-local mode:

```powershell
cd website
npm ci
$env:PUBLIC_COSHEAF_RUNTIME_MODE = "live-local"
$env:PUBLIC_COSHEAF_API_BASE = "http://127.0.0.1:8765"
npm exec -- astro dev --host 127.0.0.1 --port 4321
```

For POSIX shells:

```bash
cd website
npm ci
PUBLIC_COSHEAF_RUNTIME_MODE=live-local \
PUBLIC_COSHEAF_API_BASE=http://127.0.0.1:8765 \
npm exec -- astro dev --host 127.0.0.1 --port 4321
```

Open:

```text
http://127.0.0.1:4321/
```

If the frontend cannot read the live API, it falls back all at once to committed
fixture data and shows a fallback banner. Do not treat fixture fallback as live
repository state.

Useful live checks:

```powershell
curl.exe http://127.0.0.1:8765/api/health
curl.exe http://127.0.0.1:8765/api/status
curl.exe http://127.0.0.1:8765/api/audit/recent
```

## Write-Capable Local Mode

The server command still includes `--readonly`; that flag is the loopback server
startup guard. Confirmed Workbench actions may still perform narrowly scoped
repository writes when the action class allows it.

Expected write flow:

1. Open the relevant Workbench page.
2. Fill the form.
3. Run preview.
4. Read planned files, warnings, blockers, validation or gate state, and the
   required confirmation text.
5. Confirm only when the preview matches the intended repository change.
6. Inspect the result and the audit entry.
7. Check `git status --short` before committing.

Write-capable pages include:

- `/issues/create/`, `/issues/<issue_id>/edit/`, and `/issues/<issue_id>/` for
  local issue create, update, and close.
- `/artifacts/create/` and `/artifacts/<artifact_id>/edit/` for draft or
  pre-accepted artifact writes.
- `/artifacts/<artifact_id>/sources/` and
  `/artifacts/<artifact_id>/evidence/` for source and evidence metadata.
- `/context/<issue_id>/` for context-pack preview and build.
- `/gates/` for validate and gate runs.
- `/issues/<issue_id>/review-packet/` and
  `/artifacts/<artifact_id>/review-packet/` for informational review packets.
- `/artifacts/<artifact_id>/review-decision/` for explicit human review
  decisions.
- `/artifacts/<artifact_id>/promotion/` for accepted, refuted, or obsolete
  promotion actions.
- `/forge/submit/` for local branch, commit, push, and PR preparation.
- `/forge/pr-status/` for read-only GitHub PR collaboration status.

Direct accepted artifact creation is refused. Direct browser YAML mutation is
forbidden. Skipped, unavailable, and not-run checks are not pass.

## GitHub And Forge Setup

The browser must never hold GitHub tokens. GitHub credentials belong in backend
or operator tooling only.

Check local GitHub CLI state before using CLI forge flows:

```powershell
gh --version
gh auth status --hostname github.com
git remote -v
```

The default localhost server does not configure a server-side
`ForgeCredentialProvider`, so confirmed GitHub issue/PR create endpoints may
return `401 auth_required`. Local branch, commit, and push actions can still run
through the local forge endpoints after preview and confirm.

CLI forge commands are available for operator workflows:

```powershell
python -m cosheaf.cli forge status --json
python -m cosheaf.cli forge branch create web-workbench-demo --confirm --json
git add <intended-files>
python -m cosheaf.cli forge commit --message "Describe the change" --confirm --json
python -m cosheaf.cli forge push --branch web-workbench-demo --confirm --json
python -m cosheaf.cli forge pr create --base main --head web-workbench-demo --draft --confirm --json
```

`forge branch create` refuses `main` and `master`. `forge commit` refuses the
current `main` or `master` branch and refuses ambiguous untracked or unstaged
state. `forge push` refuses protected branches. `forge pr submit` can run the
validation/gate/push/PR flow in one confirmed CLI action for a non-protected
head branch:

```powershell
python -m cosheaf.cli forge pr submit --base main --head web-workbench-demo --draft --confirm --json
```

GitHub issue, PR, review, CI, and merge states are collaboration signals. They
are not Cosheaf human review, source metadata, verifier pass, gate pass,
accepted status, refutation, or promotion authority.

## Human Review Workflow

Use the review decision page only after the artifact, dependencies, sources,
evidence, gate state, and limitations have been inspected by a human reviewer.

The confirmed decision request must include:

- a non-AI reviewer name;
- review notes;
- scope and limitations;
- dependency, source, evidence, and gate-state acknowledgements; and
- explicit human confirmation.

AI, Codex, agent, provider, model, and verifier reviewer identities are refused.
Allowed decisions may update only the target artifact review state according to
repository policy. They do not set `status: accepted`, pass gates, mutate
verifier evidence, or promote knowledge.

## Promotion Workflow

Use the promotion page only after human review and policy checks are ready.
Promotion preview recomputes readiness and shows blockers before any lifecycle
write.

Accepted promotion requires:

- an eligible artifact target;
- repository validation;
- gatekeeper policy pass with no blocking issues;
- required verifier evidence when policy requires it;
- no failed or errored required verifier result;
- skipped verifier output treated as blocking where a pass is required;
- source metadata when public policy requires it;
- accepted or external dependencies;
- `review.state: human_reviewed` or `accepted`;
- a configured local actor;
- the exact typed confirmation phrase; and
- a non-empty promotion justification.

Confirmed promotion writes lifecycle YAML through `cosheaf.app` and service
policy. The promotion justification is recorded in the audit entry as operator
notes, not as proof in artifact YAML.

## PR Workflow

For a local web-assisted PR:

1. Start the localhost server with a local actor.
2. Start the website in `live-local` mode.
3. Open `/forge/submit/`.
4. Create or select a non-protected branch.
5. Preview commit. Use explicit backend staging only when the previewed file set
   is exactly the intended change.
6. Confirm commit after validation and gate pass.
7. Preview and confirm push for the non-protected branch.
8. Create a draft PR through a backend credential provider, or use the CLI forge
   / `gh` fallback when running from the default localhost server.
9. Open `/forge/pr-status/` to inspect GitHub collaboration state.
10. Record any Cosheaf human review separately through the Workbench review
    workflow when needed.

Before opening a PR, run verification as one batch and inspect the summary:

```powershell
$ErrorActionPreference = 'Continue'
$results = @()
function Run-Step($name, $scriptBlock) {
  Write-Host "== $name =="
  & $scriptBlock
  $code = $LASTEXITCODE
  if ($null -eq $code) { $code = 0 }
  $script:results += [pscustomobject]@{ name = $name; exit = $code }
}
Run-Step 'make lint' { make lint }
Run-Step 'make typecheck' { make typecheck }
Run-Step 'make test' { make test }
Run-Step 'make validate' { make validate }
Run-Step 'make gate' { make gate }
Push-Location website
Run-Step 'website npm ci' { npm ci }
Run-Step 'website npm test' { npm test }
Run-Step 'website npm run build' { npm run build }
Pop-Location
Run-Step 'git diff --check' { git diff --check }
Write-Host '== summary =='
$results | Format-Table -AutoSize
$failed = @($results | Where-Object { $_.exit -ne 0 })
if ($failed.Count -gt 0) { exit 1 }
```

## Audit Log Inspection

Workbench action audit entries are written under:

```text
.cosheaf/audit/web-actions.jsonl
```

Inspect recent entries:

```powershell
Get-Content .cosheaf\audit\web-actions.jsonl -Tail 20
```

Audit records should show action kind, preview/confirm mode, actor label,
result status, redacted action flags, planned/written files, and operator notes
where applicable. They must not contain GitHub tokens, authorization headers,
private keys, cookies, or hidden reasoning.

The audit log is not accepted authority. It proves that a Workbench action was
attempted or completed, not that a theorem, refutation, source claim, human
review, verifier pass, or promotion is mathematically correct.

## Recovery From Failed Actions

When preview fails, no repository write should have happened. Fix the payload or
repository state and preview again.

When confirm fails:

1. Read the user-facing error code and message.
2. Inspect `.cosheaf/audit/web-actions.jsonl` for the refused action.
3. Run `git status --short`.
4. If validation or gate failed, inspect the validation output or
   `.cosheaf/reports/`.
5. Fix the repository state and rerun preview before confirming again.

When a forge flow stops partway through, inspect each boundary separately:

```powershell
git status --short --branch
git log -1 --pretty=fuller
gh pr status
```

Do not retry by manually editing accepted artifacts, bypassing preview, storing
tokens in the browser, or marking skipped checks as pass. If generated runtime
directories were created during diagnosis, remove them before committing unless
the task explicitly asks to preserve them:

```powershell
$repo = (Resolve-Path '.').Path
foreach ($relative in @('.cosheaf', 'context\TASKS', 'website\dist', 'website\.astro')) {
  if (Test-Path -LiteralPath $relative) {
    $target = (Resolve-Path -LiteralPath $relative).Path
    if (-not $target.StartsWith($repo, [System.StringComparison]::OrdinalIgnoreCase)) {
      throw "Refusing to remove outside repo: $target"
    }
    Remove-Item -LiteralPath $target -Recurse -Force
  }
}
```

Use this guarded pattern when deleting from a script or non-interactive task.

## Security Limitations

- The localhost server is for loopback use only.
- `--local-actor` is an audit label, not authentication.
- Hosted auth is a guard stub, not production SaaS auth.
- Browser-side GitHub token storage is forbidden.
- Static showcase fixture data must be public/demo safe.
- Workbench output is display or workflow context only.
- GitHub PR approval, CI success, and PR merge are not Cosheaf human review.
- Gate pass is not proof or accepted status.
- Verifier pass is not semantic alignment unless the artifact separately records
  reviewed alignment evidence.
- Skipped, unavailable, and not-run checks are not pass.
- Accepted public artifacts still require source metadata and human review.
- Accepted/refuted/obsolete lifecycle changes must go through the promotion
  workflow, not direct YAML moves.

## Related Docs

- [Web Workbench Scope And Data Contract](WEBSITE.md)
- [Website Server API](SERVER_API.md)
- [Authentication And Authorization](AUTH.md)
- [Forge Planning, Local Git, And GitHub Actions](FORGE.md)
- [Static Website Deployment](DEPLOYMENT.md)
- [Authority Boundaries](AUTHORITY_BOUNDARIES.md)
