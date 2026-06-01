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

The `validate` and `gate` targets are scaffold-only placeholders at this stage. They report that artifact validation and gatekeeper enforcement are not implemented yet.

Use the CLI:

```bash
cosheaf --help
cosheaf version
```
