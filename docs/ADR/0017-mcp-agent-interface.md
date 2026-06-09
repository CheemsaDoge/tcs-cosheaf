# ADR 0017: Optional MCP Adapter Interface And Security Model

## Status

Accepted

## Context

ADR 0015 and ADR 0016 make CLI the first agent interface. The repository also
has an already-merged minimal read-only stdio MCP surface. The fixed plan does
not require reverting that code, but it reclassifies MCP as an optional adapter
over services rather than the primary `v0.2.1` path.

MCP can make TCS-Cosheaf easier for assistants that support resources/tools but
do not have shell access. It must not turn external agents into trusted
maintainers, proof checkers, human reviewers, or arbitrary shell operators.

## Decision

Treat MCP as an optional adapter with these constraints:

1. The current MCP server mode is stdio and local.
2. MCP resources expose context and data, not authority.
3. MCP tools are whitelisted typed service calls, not shell commands.
4. MCP prompts are workflow templates and cannot override repository policy.
5. Controlled-write tools, if added later, require explicit allow-write server
   configuration and human confirmation or explicit per-call approval.
6. Direct accepted promotion and direct accepted-path writes remain forbidden.
7. Tool outputs use structured content where possible.
8. Private KB exposure requires request-level policy mode and a configured
   private-root allowlist.
9. MCP is not required for CLI agent workflows, hosted provider work, or the
   `v0.2.1` release candidate.

## Resource Boundary

MCP resources may expose bounded, policy-filtered metadata such as workspace
info, public memory cards, issue-scoped context pack files, retrieval audit
metadata, validation summaries, gate summaries, formal-link metadata, task
metadata, and bundle metadata.

Resources do not grant permission. Reading a context pack or gate result over
MCP does not count as validation, human review, proof, verifier pass, or
accepted promotion.

Public-mode resources must exclude private artifact IDs, private artifact text,
private-derived summaries, provider credentials, environment dumps, and
secrets.

## Tool Boundary

Read-only tools may call existing services for workspace inspection,
validation, gate execution, memory search, context build, context display, and
orchestrator planning. These tools may produce runtime reports under ignored
sidecar directories, but they must not change source-of-truth artifacts.

Controlled-write tools are later optional additions. They may create draft
artifacts, task records, worker bundles, proposal records, or reducer/review
context only when the server is configured for write tools and the operator
confirms the specific action.

Forbidden MCP tools include arbitrary shell, arbitrary filesystem read/write,
environment or credential dumping, direct accepted promotion, direct
accepted-path writes, verifier-result mutation outside verifier adapters,
human-review marking, and any tool that bypasses validation, gates, review,
reducer, or promotion workflow.

## Private Context Policy

Private KB exposure through MCP requires:

1. the server configuration allowlists the private root name or path;
2. the request uses `policy_mode=private_research`;
3. the operation has explicit operator confirmation or configured consent;
4. the tool validates root scopes before retrieval or context construction;
5. structured output labels private root scopes and risk flags.

Retrieval score, PageRank, issue references, or pinned artifacts must not
bypass scope filters. Public-mode provider-send previews should use public KB
scope only.

## Structured Output

MCP tools should prefer structured content derived from service DTOs. Expected
errors should use the standard `ErrorResult` shape with `code`, `message`,
`remediation`, and `blocking`. Denied, skipped, and unavailable results are not
passes.

## Consequences

The already-merged read-only MCP surface may stay as optional adapter code if
it remains constrained and tested. Controlled-write MCP should wait until CLI
agent workflows and provider boundaries are stable, unless the maintainer
explicitly approves a narrower earlier task.

MCP code should call the service layer directly. It should not shell out to the
CLI for core behavior, expose arbitrary shell, or create a second policy path.

## Non-Goals

This ADR does not:

- make MCP the primary agent interface;
- make MCP a `v0.2.1` blocker;
- add hosted provider transport;
- add network listeners;
- add controlled-write tools;
- change artifact schema;
- change validation, gate, verifier, review, or accepted-promotion behavior;
- permit MCP to write accepted knowledge;
- make AI or MCP output count as human review.
