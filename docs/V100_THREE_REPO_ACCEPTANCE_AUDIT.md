# v1.0.0 Three-Repo Acceptance Audit

Date: 2026-06-18

Issue: #490

Branch: `v100-three-repo-acceptance-audit`

## 1. Scope

This is a documentation-only acceptance audit for the published `v1.0.0` TCS-
Cosheaf three-repository baseline.

The audit checks that:

1. `tcs-cosheaf` `v1.0.0` can be installed from the Git tag.
2. `tcs-cosheaf-workspace-template` works as the real user-facing entry point.
3. `tcs-kb-public` still preserves public, citable, human-reviewed knowledge
   boundaries.
4. Gate pass, verifier pass, and AI/operator output are not treated as accepted
   authority.
5. Current documentation does not overclaim automatic theorem proving,
   automatic promotion, default hosted workers, or Lean semantic alignment.

This audit does not change code, schemas, KB artifacts, accepted status, or
promotion rules.

## 2. Repositories Inspected

| Repository | Local commit inspected | Open PRs | Open issues during audit |
| --- | --- | ---: | ---: |
| `tcs-cosheaf` | `9adad6ba06c99607b14a6764ad29efb752bf5bb6` | 0 | 1, this audit issue #490 |
| `tcs-cosheaf-workspace-template` | `314c1edf3b5bee32f42fcab8d37e0a4852e58af3` | 0 | 0 |
| `tcs-kb-public` | `d9956e96dd20394f7c871548a04a30ebabbad744` | 0 | 0 |

All three local checkouts were clean before the audit commands. Generated
runtime outputs were not committed.

## 3. Version / Release Evidence

The GitHub release exists:

```text
tagName: v1.0.0
name: v1.0.0 AI Math Collaborator MVP
url: https://github.com/CheemsaDoge/tcs-cosheaf/releases/tag/v1.0.0
isDraft: false
isPrerelease: false
```

The framework package installed from the tag in a temporary virtual
environment:

```bash
python -m pip install "git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v1.0.0"
cosheaf version --json
```

Result:

```json
{
  "schema_version": 1,
  "package": "tcs-cosheaf",
  "version": "1.0.0"
}
```

`cosheaf interface list --json` from that tag-installed environment reported:

- `package: tcs-cosheaf`;
- `version: 1.0.0`;
- `target_release: v1.0.0`;
- 20 stable CLI surface entries;
- 2 compatibility aliases; and
- optional adapter surfaces for `provider real-run`, `mcp`, and external
  verifier execution.

The interface manifest authority notice states that interface discovery does
not grant proof, source metadata, human review, verifier pass, gate pass,
accepted status, accepted theorem/refutation status, or promotion authority.

Local shell note: an intermediate attempt to capture the JSON output with
PowerShell `Set-Content -Encoding UTF8NoBOM` failed because this shell does not
support that encoding name. The `cosheaf interface list --json` command was
rerun successfully; the capture failure was a PowerShell redirection issue, not
a Cosheaf acceptance failure.

## 4. Commands Run

### `tcs-cosheaf`

```bash
make lint
make typecheck
make test
make validate
make gate
python -m pip install "git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v1.0.0"
cosheaf version --json
cosheaf interface list --json
```

Additional release and documentation checks:

```bash
gh release view v1.0.0 --json tagName,isDraft,isPrerelease,url,name
gh pr list --state open --limit 20 --json number,title
gh issue list --state open --limit 20 --json number,title
rg -n "automatic theorem proving|automatic accepted promotion|default hosted|hosted worker|Lean.*semantic alignment|semantic alignment|AI-as-human-review|gate pass|verifier pass|accepted status|promotion authority|skipped.*pass" README.md docs context -g "*.md"
```

### `tcs-cosheaf-workspace-template`

```bash
make demo
make ai-math-collaborator-demo
make workspace-info
make validate
make gate
make pr-checklist
make context
```

Additional release and documentation checks:

```bash
gh pr list --state open --limit 20 --json number,title
gh issue list --state open --limit 20 --json number,title
rg -n "v1\.0\.0|hosted provider|accepted write|promotion|human-review|skipped.*pass|Lean|semantic alignment|automatic theorem" README.md docs scripts Makefile .github -g "*.md" -g "*.sh" -g "*.ps1" -g "Makefile" -g "*.yml"
```

### `tcs-kb-public`

```bash
cosheaf version --json
python scripts/check_public_kb_policy.py
cosheaf workspace info
cosheaf validate
cosheaf gate run
cosheaf gate run --pr-checklist .github/pull_request_template.md
```

Additional policy and documentation checks:

```bash
gh pr list --state open --limit 20 --json number,title
gh issue list --state open --limit 20 --json number,title
rg -n "human review|source metadata|gate success|validation.*substitute|accepted|AI output|verifier pass|Lean|semantic alignment|automatic theorem|promotion" README.md docs .github scripts kb/public/accepted reviews -g "*.md" -g "*.py" -g "*.yml" -g "*.yaml"
```

## 5. Results

### Framework

- `make lint`: passed.
- `make typecheck`: passed for 234 source files.
- `make test`: passed, 849 tests.
- `make validate`: passed, checked 20 YAML records.
- `make gate`: passed.
- Tag install from `v1.0.0`: passed in a temporary virtual environment.
- `cosheaf version --json`: reported `1.0.0`.
- `cosheaf interface list --json`: reported the `v1.0.0` interface manifest
  with stable CLI surfaces and explicit non-authority language.

### Workspace Template

- `make demo`: passed. It installed `tcs-cosheaf` from the published
  `v1.0.0` tag, inspected the workspace, validated, ran gates, ran the PR
  checklist gate, and built context for `issue.example-private-claim`.
- `make ai-math-collaborator-demo`: passed. In this local checkout layout the
  script used the sibling framework checkout, which is currently `1.0.0`; the
  default published-tag path remains available when no sibling checkout is
  present or when `COSHEAF_FRAMEWORK_REF` is set explicitly.
- `make workspace-info`: passed. The workspace showed a readonly public root
  and writable private root:
  - public: `kb/public`, `readonly=true`, `priority=10`;
  - private: `kb/private`, `readonly=false`, `priority=20`.
- `make validate`: passed, checked 3 YAML records.
- `make gate`: passed.
- `make pr-checklist`: passed.
- `make context`: passed and built `context/TASKS/issue.example-private-claim`.

The AI Math Collaborator demo output stated that no hosted provider, MCP
requirement, accepted write, promotion, public KB write, or human-review
spoofing was performed. It also stated that skipped optional rows are recorded
as skipped, not pass.

### Public KB

- `cosheaf version --json`: reported `1.0.0`.
- `python scripts/check_public_kb_policy.py`: passed.
- `cosheaf workspace info`: passed.
- `cosheaf validate`: passed, checked 22 YAML records.
- `cosheaf gate run`: passed.
- `cosheaf gate run --pr-checklist .github/pull_request_template.md`: passed.

The public KB repository is writable to maintainers in its own checkout, but
downstream workspaces mount public KB content readonly. Public KB acceptance
remains a reviewed repository workflow, not a gate-only or verifier-only
workflow.

## 6. Authority Boundaries Checked

The audit found the expected conservative boundaries:

- `validate` and `gate` remain checks, not accepted status.
- Skipped, unavailable, unsupported, and inconclusive rows remain non-pass
  states.
- Verifier pass is checker evidence only; it does not create source metadata,
  human review, accepted status, or promotion authority.
- AI, operator, workflow, research-loop, campaign, benchmark, comparison, MCP,
  and static-report outputs remain review context or sidecar guidance only.
- Public KB accepted artifacts still require source metadata and human review.
- `tcs-kb-public` policy guard checks reject attempts to use operator,
  workflow, research-loop, cross-check, campaign, or model output as source
  metadata, human review, verifier pass, accepted proof/status/refutation, or
  promotion authority.
- Formal links remain metadata unless a real checker result records otherwise.
- Lean external-library reference checks, when available, check only import and
  symbol resolution; they do not prove informal/formal semantic alignment.
- Hosted provider paths remain explicit/default-off. The stable demo path does
  not require hosted LLMs, API keys, or network provider calls.

The documentation searches found limitation and policy language rather than a
release-blocking overclaim.

## 7. Known Limitations

- `v1.0.0` is a CLI-first AI Math Collaborator MVP baseline, not production
  SaaS.
- There is no web UI.
- There is no automatic theorem proving.
- There is no automatic accepted promotion.
- There is no AI-as-human-review.
- There is no default hosted provider or default hosted worker execution path.
- There is no full Lean/mathlib/CSLib integration.
- There is no automatic informal/formal semantic-alignment checking.
- Optional SAT, SMT, Lean, lake, and external checker paths may remain skipped
  when unavailable; skipped is not pass.
- Runtime outputs are written under ignored `.cosheaf/` paths or generated
  context-pack paths. They were not committed by this audit.

## 8. Decision

ACCEPTED:

`v1.0.0` passes three-repository acceptance as a CLI-first AI Math Collaborator
MVP baseline.

The next recommended work is showcase / website / public explanation, focused
on demonstrating the workspace-template demo path, the three-repository model,
accepted/draft boundaries, and the rule that AI output cannot directly accept
knowledge.
