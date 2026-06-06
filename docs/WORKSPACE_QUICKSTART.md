[中文版](WORKSPACE_QUICKSTART.zh-CN.md) | [English](WORKSPACE_QUICKSTART.md)

# Workspace Quickstart

This guide shows the recommended end-to-end workspace shape for using the
framework package, the public KB, and private research together.

## Recommended Layout

`tcs-cosheaf` is the runtime package. It is installed into the Python
environment and should not be copied into a research workspace.

One practical workspace layout is:

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

With this layout, configure the public KB root to the public KB subtree:

```toml
[workspace]
name = "my-tcs-workspace"

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

[policy]
private_can_depend_on_public = true
public_can_depend_on_private = false
accepted_requires_source = true
```

The workspace template uses the shorter `kb/public` path by default. That is
also valid when `kb/public` is replaced by, or mounted from, the public KB
contents.

```text
workspace/
|-- cosheaf.toml
`-- kb/
    |-- public/
    `-- private/
```

In both layouts, public KB roots are readonly for downstream workspaces and
private KB roots are writable.

## Install Runtime

Install the framework package into the active environment:

```bash
python -m pip install "git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.1.1"
```

For framework development, clone `tcs-cosheaf` separately and install it with
development dependencies. Do not turn the framework checkout itself into the
user-private research workspace.

## Validation

From the workspace root, inspect the active roots and run the normal local
checks:

```bash
cosheaf workspace info
cosheaf validate
cosheaf gate run
cosheaf index rebuild
```

The expected dependency direction is:

```text
private artifact -> public artifact
```

Public artifacts must not depend on private artifacts. Accepted artifacts must
not depend on draft or otherwise pre-accepted artifacts, even across KB roots.

## Common Workflow

1. Draft private or experimental material under `kb/private/`.
2. Keep conjectures, failed attempts, unpublished ideas, and local research
   notes private.
3. Run validation, gatekeeper, and context-pack commands from the workspace
   root.
4. Review and promote only when the artifact satisfies the repository policy.
5. Move reusable public material into `tcs-kb-public` through a separate
   source-reviewed public KB issue and pull request.
6. Keep the public KB mounted readonly in downstream workspaces.

## Public Knowledge Policy

Public KB repositories are intended for reusable, citable knowledge artifacts.
They should not contain private conjectures, unpublished research ideas, or
accepted LLM-generated artifacts without human review.

Accepted public artifacts require source metadata and human review. Proof
sketches in the public KB are explanatory source-reviewed artifacts, not
machine-checked proofs and not Lean verification evidence.

## Migrating From Legacy Layout

Older single-repository workspaces may have only:

```text
workspace/
`-- kb/
```

The recommended layout separates private work from readonly public knowledge:

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

Migration steps:

1. Add `cosheaf.toml` with one readonly public root and one writable private
   root.
2. Move private drafts, conjectures, experiments, and unreviewed material under
   `kb/private/`, preserving lifecycle subdirectories such as `draft/` and
   `accepted/` when their status already matches policy.
3. Mount or clone `tcs-kb-public` as the readonly public root.
4. Do not copy private accepted artifacts into the public KB. Reusable public
   material should be proposed in `tcs-kb-public` through a separate reviewed
   PR.
5. Run `cosheaf workspace info`, `cosheaf validate`, `cosheaf gate run`, and
   `cosheaf index rebuild` before relying on the migrated workspace.

If a repository has no `cosheaf.toml`, Cosheaf preserves legacy mode with one
writable KB root at `kb/`.
