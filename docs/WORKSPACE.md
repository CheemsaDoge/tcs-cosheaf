# Workspace Model

TCS-Cosheaf workspaces are configured by an optional `cosheaf.toml` file at the
repository root. If the file is absent, commands preserve the legacy
single-repository behavior and load one writable KB root at `kb/`.

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

## Layering Rules

Loaded records retain their source KB root name, root path, readonly flag, and
path relative to that root. Validation and gates enforce:

- Artifact IDs are globally unique across all roots.
- Private artifacts may depend on public artifacts.
- Public artifacts must not depend on private artifacts.
- Accepted artifacts must not depend on draft or pre-accepted artifacts, even
  across KB roots.
- Status/path rules are evaluated relative to each KB root.
- Readonly roots cannot be modified by lifecycle write commands.

## Legacy Mode

Without `cosheaf.toml`, the active KB root is:

```text
default | kb | readonly=false | priority=0
```

This preserves existing single-repository behavior for current users and tests.
