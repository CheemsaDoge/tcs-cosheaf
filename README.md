# tcs-cosheaf

TCS-Cosheaf is a Git-backed research knowledge base and agent harness for theoretical computer science. It is intended to manage typed research artifacts and the verification workflow around them.

Current status: pre-MVP scaffold.

See [AGENTS.md](AGENTS.md) for project-wide engineering rules.

## Development

This project targets Python 3.11+.

Install the development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the intended local checks:

```bash
make lint
make typecheck
make test
make validate
make gate
```

The `validate` target runs repository validation for YAML/model parsing, ID
uniqueness, status/path consistency, dependency checks, and local evidence path
checks. The `gate` target runs the gatekeeper, writes reports under
`.cosheaf/reports/`, and reports not-yet-implemented gates as skipped rather
than pretending they passed.

Use the CLI:

```bash
cosheaf --help
cosheaf version
cosheaf validate
cosheaf gate
```
