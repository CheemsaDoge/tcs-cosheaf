# Comparison Reports

V17 adds deterministic comparison reports for existing workflow, campaign, and
benchmark records:

```bash
cosheaf compare workflows <before-id> <after-id> --json
cosheaf compare campaigns <before-id> <after-id> --json
cosheaf compare benchmarks <before-id> <after-id> --json
```

These commands read existing runtime records and emit metric-scoped deltas.
They do not write accepted knowledge, create human review, fabricate source
metadata, mark verifier or gate pass, call hosted providers, execute shell
commands, or promote artifacts.

Safety regressions are reported separately. A newer run is not globally better
just because one metric improves; any increase in authority, private-leak,
blocking, failed, or skipped counts must be reviewed in context.
