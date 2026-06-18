# Local Issues

Cosheaf local issues are repository YAML records under `issues/`. They are
workflow memory for local research and implementation tasks, independent of
GitHub issues.

## Layout

- `issues/open/<issue-id>.yaml`
- `issues/blocked/<issue-id>.yaml`
- `issues/closed/<issue-id>.yaml`

`cosheaf issue create` writes new records under `issues/open/`.
`cosheaf issue close` moves an open or blocked record to `issues/closed/`.

## Model

The current first-class issue fields are:

- `id`
- `type: issue`
- `title`
- `status: open | blocked | closed`
- `summary`
- `created_at`
- `updated_at`
- `authors`
- `labels`
- `related_artifacts`
- `related_sources`
- `parent_issue` optional
- `external_links` optional
- `scope: private | public`
- `close_reason` optional for closed issues

For compatibility, the loader still accepts older issue YAML that uses
`description` instead of `summary`, `tags` instead of `labels`, and optional
`severity`. New writes use `summary` and `labels`.

## CLI

```bash
cosheaf issue create --title <title> --id <id> --json
cosheaf issue show <id> --json
cosheaf issue list --json
cosheaf issue close <id> --reason <reason> --json
```

All issue commands are local filesystem operations. They do not call GitHub,
require a GitHub token, create remote issues, update pull requests, run
verifiers, run gates, promote artifacts, or change artifact lifecycle status.

Closing an issue records workflow completion only. It does not mean any related
artifact is accepted, refuted, human-reviewed, verifier-passed, or gate-passed.

## Validation And Context

Issue YAML is loaded through `cosheaf.storage.loader.IssueRecord`. Repository
validation rejects invalid issue status values and unknown fields through the
same schema/model gate used for other YAML records.

Context packs already resolve issue records by ID. A local issue can reference
artifacts through `related_artifacts`; `cosheaf context build <issue-id>` uses
that local issue record as context input. Future adapters that synchronize with
GitHub must treat the local YAML record as distinct from the remote issue and
must not infer artifact acceptance from either side.
