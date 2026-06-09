# ADR 0017: MCP Agent Interface And Security Model

## Status

Proposed

## Context

ADR 0015 sets the post-`v0.2.0` direction toward agent access through MCP,
Skill guidance, and hosted API workers. ADR 0016 defines the general
agent-access authority model and threat model. The repository now has a thin
service layer, agent-access DTOs, and a provider-send context preview policy
service. Before implementing an MCP server, the project needs a durable MCP
boundary that preserves public/private KB policy, accepted-promotion policy,
and the CLI/gate review model.

MCP should make TCS-Cosheaf easier for external agents to use. It must not
turn external agents into trusted maintainers, proof checkers, human reviewers,
or arbitrary shell operators.

## Decision

Adopt an MCP server design with these constraints:

1. The first MCP server mode is stdio.
2. MCP resources expose context and data, not authority.
3. MCP tools are whitelisted typed service calls, not shell commands.
4. MCP prompts are workflow templates and cannot override repository policy.
5. Controlled-write tools require both server allow-write configuration and
   human confirmation or explicit per-call approval.
6. Direct accepted promotion and direct accepted-path writes remain forbidden.
7. Tool outputs use structured content where possible.
8. Private KB exposure requires request-level policy mode and a configured
   private-root allowlist.

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
validation, gate execution, memory search, context build, provider context
preview, task listing, and bundle validation. These tools may produce runtime
reports under ignored sidecar directories, but they must not change
source-of-truth artifacts.

Controlled-write tools are later-phase additions. They may create draft
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

The MCP implementation should start with a read-only stdio server and a small
tool/resource set. Controlled-write tools should be implemented only after
read-only behavior and security regression tests are stable.

MCP code should call the service layer directly. It should not shell out to the
CLI for core behavior, expose arbitrary shell, or create a second policy path.

This ADR does not implement the MCP server. It records the design boundary for
future tasks.

## Non-Goals

This ADR does not:

- implement MCP runtime code;
- add MCP dependencies;
- add hosted provider transport;
- add network listeners;
- add controlled-write tools;
- change artifact schema;
- change validation, gate, verifier, review, or accepted-promotion behavior;
- permit MCP to write accepted knowledge;
- make AI or MCP output count as human review.

