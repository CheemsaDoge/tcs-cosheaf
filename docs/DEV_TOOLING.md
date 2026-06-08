# Developer Tooling

Developer tools in this document are optional aids for local maintainers. They
are not runtime dependencies and are not project truth. Artifact YAML, source
metadata, verifier evidence, gate reports, human review, and explicit promotion
remain authoritative.

## CodeGraph

CodeGraph may be used only as developer-only, local-only code navigation and
impact-analysis tooling. It can help a maintainer inspect implementation
relationships or choose likely affected tests, but it must not feed artifact
truth, retrieval ranking, gates, context generation, verifier results, review
records, or promotion.

The repository includes a safe availability probe:

```bash
python scripts/dev/codegraph_probe.py --json
```

If CodeGraph is unavailable, the probe reports `status: unavailable` and
`fallback: run_full_verification` with exit code 0. Use `--strict` only when a
manual developer task intentionally wants absence to be a nonzero result. Core
CI, validation, gates, and runtime commands must continue to work without
CodeGraph installed.

Generated CodeGraph files must stay sidecar/cache only. The intended locations
are `.codegraph/` or `.cosheaf/dev/codegraph/`, both of which are gitignored.
Do not commit generated graph databases, indexes, dashboards, or impact hints.

CodeGraph output is not evidence. It cannot justify accepting knowledge,
skipping tests, weakening gates, changing retrieval scores, or marking review
as human-reviewed. When in doubt, run the full verification ladder:

```bash
make lint
make typecheck
make test
make validate
make gate
```

## Headroom

Headroom is scaffolded only as a default-off developer experiment for
noncanonical text views such as long logs, stdout/stderr sidecars, and temporary
developer-facing tool-output views. It is not part of runtime, CI, retrieval,
validation, gates, verifier evidence, review, artifact YAML, accepted KB, or
promotion.

The repository includes a conservative boundary probe:

```bash
python scripts/dev/headroom_probe.py --source .cosheaf/logs/example.stdout.txt --json
python scripts/dev/headroom_probe.py --enable --source .cosheaf/logs/example.stdout.txt --json
```

Without `--enable`, the probe reports `status: disabled` and exits 0. With
`--enable`, it first checks that the source path is an approved noncanonical
input. Missing Headroom reports `status: unavailable`, `fallback:
use_original_text`, and exits 0 unless `--strict` is set. The current scaffold
records tool availability and policy metadata only; it does not run an actual
Headroom compression command.

Allowed source paths are intentionally narrow:

- `.cosheaf/logs/`
- `.cosheaf/tasks/.../stdout.txt`
- `.cosheaf/tasks/.../stderr.txt`
- `.cosheaf/orchestrator/.../stdout.txt`
- `.cosheaf/orchestrator/.../stderr.txt`
- `.cosheaf/dev/headroom/`

The probe refuses canonical or governance inputs, including `AGENTS.md`,
`docs/CODEX_WORKFLOW.md`, ADRs, `kb/`, `reviews/`, `sources/`, schemas,
artifact YAML, gate reports, retrieval audit files, memory sidecars, and index
outputs. It never runs a learning/write-back mode, never rewrites the source
file, and always falls back to the original text.

Generated Headroom files must stay sidecar/cache only. The intended locations
are `.headroom/` and `.cosheaf/dev/headroom/`, both of which are gitignored.
Do not commit compressed summaries, learned state, caches, or experiment
metadata unless a later focused policy explicitly makes a particular artifact
reviewable.

## Understand-Anything

Understand-Anything may be used only as an isolated manual onboarding aid for
developers who want a visual map of the framework code or public documentation.
It is not a runtime dependency, package dependency, validation input, gate
input, retrieval index, memory sidecar, verifier result, review record, or
accepted-knowledge source.

Use it only on sanitized local copies. If a checkout may contain private KB
records, unpublished research, local paths, secrets, or sensitive `.cosheaf/`
runtime output, first create a scrubbed copy that excludes those paths. A safe
manual workflow is:

```bash
git clone https://github.com/CheemsaDoge/tcs-cosheaf.git tcs-cosheaf-ua-sanitized
cd tcs-cosheaf-ua-sanitized
git clean -xdf
```

Then run Understand-Anything according to its own local documentation from that
sanitized copy. Keep any dashboard bound to `127.0.0.1` or another local-only
interface. Do not expose the dashboard on a public network, and do not upload
private KB files, unpublished source notes, generated context packs, run logs,
or machine-specific paths.

Generated Understand-Anything output must remain sidecar/cache only. The
expected local output path is `.understand-anything/`, which is gitignored. Do
not commit generated graphs, dashboards, indexes, summaries, or caches, and do
not copy them into `.cosheaf/memory/`, artifact YAML, review records, verifier
evidence, source notes, or accepted KB paths.

Manual teardown after inspection:

```bash
rm -rf .understand-anything/
git status --short
```

On Windows PowerShell:

```powershell
Remove-Item -Recurse -Force .understand-anything -ErrorAction SilentlyContinue
git status --short
```

If Understand-Anything is unavailable, no project workflow is affected. Use the
normal repository docs and full verification ladder instead.
