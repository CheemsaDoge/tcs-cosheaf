# Workspace Model

TCS-Cosheaf workspaces are configured by an optional `cosheaf.toml` file at the
repository root. If the file is absent, commands preserve the legacy
single-repository behavior and load one writable KB root at `kb/`.

## Recommended Three-Repository Setup

The framework repository is `tcs-cosheaf`. It provides the CLI, schemas, gates,
validation, verifier adapters, and agent harness. It is not the recommended
place for ordinary user-private research notes.

The reusable public knowledge base is
[`tcs-kb-public`](https://github.com/CheemsaDoge/tcs-kb-public). Downstream user
workspaces should mount it as a readonly public KB root.

The recommended user entry point is
[`tcs-cosheaf-workspace-template`](https://github.com/CheemsaDoge/tcs-cosheaf-workspace-template).
The template combines the framework package with a readonly public KB root and a
writable `kb/private` overlay. Users should not manually merge the framework
repository and KB repositories into one ad hoc tree.

The intended dependency direction is:

```text
private user artifact -> public KB artifact
```

Public KB artifacts must not depend on private artifacts. Private overlays may
depend on public artifacts when `[policy] private_can_depend_on_public = true`.

For a short end-to-end setup guide, see
[`docs/WORKSPACE_QUICKSTART.md`](WORKSPACE_QUICKSTART.md).

## Configuration

The current workspace configuration shape is:

```toml
[workspace]
name = "my-tcs-workspace"

[[kb]]
name = "public"
path = "kb/public"
readonly = true
priority = 10

[[kb]]
name = "private"
path = "kb/private"
readonly = false
priority = 20

[policy]
private_can_depend_on_public = true
public_can_depend_on_private = false
accepted_requires_source = true
```

Each KB root has:

- `name`: stable root name used in reports and loaded-record metadata.
- `path`: repository-relative path to the KB root.
- `readonly`: whether write commands may modify that root.
- `priority`: deterministic ordering and reporting priority.

Absolute paths and parent-directory traversal are rejected. KB root names and
paths must be unique.

## Command Behavior

These commands use `cosheaf.toml` by default when it exists:

- `cosheaf validate`
- `cosheaf gate` and `cosheaf gate run`
- `cosheaf context build` and `cosheaf context show`
- `cosheaf index rebuild`
- `cosheaf graph show`
- `cosheaf artifact create`
- `cosheaf artifact move-status`
- `cosheaf workspace info`

`cosheaf workspace info` prints the active mode, repository root, and KB roots.

When a configured workspace has readonly and writable roots, artifact creation
writes to the writable private root by default. Status movement refuses to
modify artifacts loaded from readonly roots.

`cosheaf artifact promote <artifact-id>` also refuses readonly KB roots. If a
public KB root is writable for maintenance and `[policy] accepted_requires_source`
is true, promotion refuses public artifacts that do not already carry complete
structured source metadata.

## Querying The SQLite Index

`cosheaf index rebuild` writes `.cosheaf/index.sqlite` from the current YAML
records. YAML remains the source of truth, so callers should rebuild the index
after repository changes before using the query API.

Minimal Python usage:

```python
from cosheaf.storage.index import rebuild_index
from cosheaf.storage.query import ArtifactIndexQuery
from cosheaf.storage.repo import RepoContext

context = RepoContext(".")
rebuild_index(context)

query = ArtifactIndexQuery.from_context(context)
all_artifacts = query.list_artifacts()
drafts = query.list_artifacts_by_status("draft")
graph_artifacts = query.list_artifacts_by_domain("graph-theory")
deps = query.list_dependencies("claim.example")
rdeps = query.list_reverse_dependencies("definition.graph")
```

Each artifact row includes `kb_root`, which is `public`, `private`, `default`,
or an empty string when the indexed record did not come from a KB root.

## Layering Rules

Loaded records retain their source KB root name, root path, readonly flag, and
path relative to that root. Validation and gates enforce:

- Artifact IDs are globally unique across all roots.
- Private artifacts may depend on public artifacts.
- Public artifacts must not depend on private artifacts.
- Accepted artifacts must not depend on draft or pre-accepted artifacts, even
  across KB roots.
- Accepted artifacts in public KB roots require complete structured source
  metadata when `accepted_requires_source = true`.
- Draft public artifacts and accepted private artifacts are not blocked solely
  for missing source metadata under the current policy.
- Status/path rules are evaluated relative to each KB root.
- Readonly roots cannot be modified by lifecycle write commands.

## Legacy Mode

Without `cosheaf.toml`, the active KB root is:

```text
default | kb | readonly=false | priority=0
```

This preserves existing single-repository behavior for current users and tests.
Legacy mode has no configured public KB root, so the accepted-public source
metadata gate reports `not_applicable`.

## Migrating From Legacy Layout

Legacy repositories usually have a single writable KB root:

```text
workspace/
`-- kb/
```

The recommended workspace layout separates user-private material from readonly
public knowledge:

```text
workspace/
|-- cosheaf.toml
|-- kb/
|   `-- private/
`-- external/
    `-- tcs-kb-public/
        `-- kb/
            `-- public/
```

Use a configured public root such as:

```toml
[[kb]]
name = "public"
path = "external/tcs-kb-public/kb/public"
readonly = true
priority = 10

[[kb]]
name = "private"
path = "kb/private"
readonly = false
priority = 20
```

The workspace template's default `kb/public` root is also valid when that path
is replaced by, or mounted from, the public KB contents.

Migration should preserve artifact meaning and status. Move private drafts,
conjectures, failed attempts, experiments, and unpublished notes under
`kb/private/`. Do not copy private material into a public KB root. Reusable
public artifacts should be proposed to `tcs-kb-public` through a separate
source-reviewed issue and pull request.

After migration, run:

```bash
cosheaf workspace info
cosheaf validate
cosheaf gate run
cosheaf index rebuild
```
