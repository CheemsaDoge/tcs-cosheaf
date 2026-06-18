# Static Reports

V17 adds static Markdown/JSON report directories for existing workflow,
campaign, and benchmark runtime records:

```bash
cosheaf report workflow <workflow-id> --out <dir> --json
cosheaf report campaign <campaign-id> --out <dir> --json
cosheaf report benchmark <run-id> --out <dir> --json
```

Each report writes:

- `summary.md`
- `metrics.json`
- `authority_findings.json`
- `memory_changes.json`
- `checker_matrix.json`
- `review_handoff_summary.md`

Reports must be written to repository-local non-accepted directories. They are
review context only: they do not write accepted knowledge, create human review,
fabricate source metadata, mark verifier or gate pass, call hosted providers,
execute shell commands, or promote artifacts.

Use `--public-only` when generating shareable review context. For workflow and
campaign reports, public-only mode rejects runtime records that contain private
KB references. Benchmark static reports use aggregate benchmark sidecars only.
