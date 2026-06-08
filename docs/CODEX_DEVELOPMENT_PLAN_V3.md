# TCS-Cosheaf longplan v3：Agent Access + Hosted API + MCP + Skill

This is the current durable Codex execution plan for post-`v0.2.0`
TCS-Cosheaf work. It supersedes `docs/CODEX_DEVELOPMENT_PLAN.md`, which is
now historical project memory only.

The task runbook below is maintainer-provided and intentionally preserved in
Chinese. If any earlier plan, stale issue, or roadmap note conflicts with this
file, this v3 plan controls unless the maintainer gives a newer explicit
instruction.

## 使用方式

本文件是给 Codex 执行的分阶段 runbook。它继承原 `longplan` 的执行形式，但约束已经改变：**API 调用、MCP、Skill、外部 agent 与内部 hosted workers 都是 v0.2.1 之后的正式目标**。不得把本计划误读为 local-only hardening 计划。

执行规则：

```text
1. 每次只执行一个 Task。
2. 一个 Task = 一个 branch = 一个 PR。
3. 完成当前 Task 后必须停止，输出 PR summary，不得继续做下一个 Task。
4. 不得直接推 main。
5. branch 名、PR 标题、issue 标题不得使用 `codex/`、`codex-` 或任何 Codex 专属前缀。
6. 如果仓库实际状态与本计划不一致，先做状态审计，再报告差异，不得自行假设。
7. 如果测试或命令无法运行，必须报告真实原因，不得伪造成功。
8. 验收仓库时不得只看文档；必须检查实际代码、测试、CI、CLI、schema 与关键运行路径。
9. 不得把 validation/gate pass 写成人工 review。
10. 不得让任何 agent、MCP tool、hosted model worker 直接写 `kb/accepted/`。
11. API 调用是计划内核心能力；不得再把 Cosheaf 限定为 local-only runtime。
12. 真实 API 调用不得进入 CI；CI 必须使用 fake/mocked provider。
13. 真实 provider 只能在显式配置、显式 consent、显式 policy scope 下调用。
14. Skill 是操作说明，不是 source of truth；MCP/API/CLI 才是工具接口。
15. 本文件不是“一次性实现整个系统”的指令。
```

---

## 0. 当前判断与回退建议

### 0.1 正确基线

本轮回退/审计基线是：

```text
repo: CheemsaDoge/tcs-cosheaf
baseline: v0.2.0
commit prefix: 9b1c3fa
meaning: v0.2.0 local-MVP release
```

说明：

```text
1. 本轮不是回退到 v0.1.1。
2. v0.1.1 只是更早的 Formal Link Layer support baseline。
3. v0.2.0 是本轮 post-v0.2.0 agent access 规划的干净基线。
4. 需要比较的是 current main 相对 v0.2.0 的 post-release 变化。
```

### 0.2 回退策略

默认采用“定向回退 + 方向重写”，不是整仓 reset。

必须审计并可能重写：

```text
1. context/CURRENT_MILESTONE.md
   如果 next focus 仍写成 local orchestrator hardening，改为：
   v0.2.1 Agent Access + Hosted API Provider + MCP/Skill milestone。

2. docs/ROADMAP.md
   如果下一阶段仍是 local-only runtime hardening，改为：
   MCP + Skill + hosted model API + external agent integration。

3. docs/CODEX_DEVELOPMENT_PLAN.md 或等价 longplan 文档
   如果仍以旧 Phase4-8 local runtime 为主线，应标记为 historical plan，
   并新增/替换为本 longplan v3。

4. open issues / stale issues
   任何只把 local orchestrator hardening 当作下一阶段主线的 issue，
   只能保留为 schema/test hardening，不得阻塞 API/MCP 主线。
```

暂不回退：

```text
1. v0.2.0 已包含的 deterministic local-MVP 能力。
2. artifact/schema/validation/gate/index/context/memory/retrieval/eval/formal-link 代码。
3. 已存在的 local orchestrator state/DAG/reducer/fake provider 代码。
4. 已存在但不默认联网、不默认 promotion、不破坏 gate 的 agent scaffold。
```

原因：这些能力可以作为 MCP tools、hosted API workers、external-agent substrate 的底座。问题不是它们存在，而是旧 roadmap 把“继续 local-only hardening”当成下一主线。

### 0.3 硬回退方案

仅当 post-v0.2.0 代码污染无法定向回退时，才从 tag 新建干净分支：

```bash
git fetch --tags
git checkout -b agent-api-mcp-from-v020 v0.2.0
```

只允许 cherry-pick：

```text
1. 非争议测试修复。
2. 非争议文档 typo 修复。
3. 与 v0.2.1 API/MCP/Skill 方向一致的安全文档。
4. 不改变 public/private、accepted/draft、gate/review/promotion 不变量的代码。
```

不得 cherry-pick：

```text
1. 把下一阶段继续写成 local-only orchestrator hardening 的文档。
2. 把 hosted provider 永久推迟、排除或降级为非目标的决策。
3. 默认自动 promotion、默认联网、默认发送 private KB 的行为。
4. 绕过 reducer/gate/review 的 agent runtime 行为。
```

---

## 1. 总目标

TCS-Cosheaf post-v0.2.0 的目标是：

```text
Git-backed research knowledge base
+ deterministic retrieval/context/gate substrate
+ mainstream agent access layer through MCP and Skill
+ first-class hosted model API worker support
+ external-agent and internal-orchestrator modes
+ protected review/promotion governance
```

不是：

```text
1. 只允许本地 worker 的封闭工具。
2. 把 Cosheaf 内部 orchestrator 永久限制为 local-only。
3. 让外部 agent 直接读全仓、乱写文件、绕过 gate。
4. 让 hosted model output 直接变成 accepted knowledge。
5. 把 MCP tool、Skill 或 AI review 当成人工 review。
6. 默认联网、默认发送 private KB、默认真实 API 调用。
7. 生产级多用户平台、Web UI、权限系统或 SaaS。
```

核心原则：

```text
repo 是 durable memory；
artifact 是知识单元，不是聊天输出；
MCP 是主流 agent 调用 Cosheaf 的机器接口；
Skill 是 agent 操作说明和约束包；
hosted model API 是计划内 worker/runtime 能力；
外部 agent 和内部 orchestrator 可以并存；
所有 agent 产物都必须进入 draft/proposal/bundle/review 流程；
accepted knowledge 只能通过 validation/gate/review/promotion 晋升。
```

---

## 2. 三仓职责边界

必须保持三仓分层，不得混用。

```text
tcs-cosheaf
  framework / CLI / schema / validation / gate / index / context pack /
  memory / MCP server / Skill package / provider gateway / task harness /
  orchestrator state / worker contracts / eval / observability

tcs-kb-public
  readonly public reusable KB；
  只存 public、citable、source-reviewed、human-reviewed 的 accepted knowledge；
  不存 private conjecture，不存未经审核的 LLM 产物；
  不承载 MCP server、provider gateway、agent runtime。

tcs-cosheaf-workspace-template
  用户入口；
  readonly public KB + writable private KB overlay；
  运行 MCP server、demo、private research、agent dry-run、hosted-worker experiments；
  不把 mounted public KB 混入 template repo。
```

严禁：

```text
1. 把 private artifact 写入 tcs-kb-public。
2. 让 public artifact 依赖 private artifact。
3. 让 worker output 直接写入 kb/accepted/。
4. 让 validation/gate pass 自动等于 accepted。
5. 让 AI review 冒充 human review。
6. 让 MCP controlled-write tool 修改 readonly public root。
7. 让 hosted provider 在未授权 policy scope 下读取 private KB。
```

---

## 3. 架构决策

### 3.1 CLI、Service、MCP、Skill、Hosted API 的职责

```text
CLI:
  人类与 CI 的稳定入口，也是测试 oracle。

Service layer:
  CLI、MCP server、internal orchestrator、hosted workers 共用的 typed API。
  禁止 MCP 通过 shell-out 复用 CLI 实现核心逻辑。

MCP:
  主流 agent 的标准工具接口，暴露 resources、prompts、tools。
  MCP tools 是白名单 service calls，不是 arbitrary shell。

Skill:
  ChatGPT/Codex-like agent 的操作手册。
  说明何时用 Cosheaf、优先用 MCP、如何 fallback 到 CLI、禁止动作、PR summary 格式。

Hosted Model API:
  Cosheaf 内部 worker runtime 的计划内能力。
  用于 reasoner、verifier、counterexampleer、explorer、formalizer、librarian_summarizer 等角色。
```

### 3.2 Orchestrator 与 Worker 模式

允许三种模式并存：

```text
Mode A: External-agent orchestrator
  Codex/Claude/Cursor/ChatGPT 通过 MCP 调用 Cosheaf。
  Cosheaf 提供 workspace info、search、context、gate、bundle validation、draft write。

Mode B: Cosheaf internal orchestrator + hosted API workers
  Cosheaf 负责编排 task DAG。
  Hosted API provider 执行 reasoner/verifier/explorer 等 worker。
  输出必须是 WorkerBundle/proposal/draft，不得直接 accepted promotion。

Mode C: Hybrid mode
  外部 agent 作为 orchestrator。
  Cosheaf 也可创建 AgentTask，并调用 hosted/local worker。
  所有产物通过同一 reducer/gate/review。
```

必须修正的旧限制：

```text
1. “Cosheaf 只做本地状态机、DAG、local dry-run、reducer”不可作为产品边界。
2. local-only 只能是 fallback/testing mode。
3. hosted API provider 必须进入正式计划和接口设计。
4. 真实 API 不进入 CI，不等于真实 API 不支持。
```

### 3.3 API 调用边界

Hosted provider 是一等规划能力，但必须受控：

```text
1. 没有 API key 时不可调用真实 provider；这不是 local-only policy。
2. 首个真实 provider transport 应支持 OpenAI-compatible 基础接口。
3. 后续可扩 Anthropic/Gemini/local/custom gateway。
4. 所有真实 provider 调用必须有 fake/mocked transport 测试。
5. API key 只读环境变量或 secret manager，不写入 repo/log。
6. 输入 context 必须走 policy filter。
7. private KB 默认不得发给未经允许的 provider。
8. 发送 private context 前必须显式 policy_mode=private_research 且显式 consent。
9. 输出必须经 schema validation，失败则 retry、repair 或生成 rejected bundle。
10. hosted verifier 不能替代 deterministic verifier 或 human review。
11. cost、latency、model、provider、prompt hash、output hash 必须进入 run log。
12. provider call 必须支持 timeout、cancellation、rate-limit handling。
```

---

## 4. 全局不可违反的不变量

### 4.1 知识生命周期

```text
1. accepted artifact 必须经过 validation、gate、review、promotion。
2. worker output 不得直接写入 kb/accepted/。
3. AI review 不等于 human review。
4. validation/gate pass 不等于 accepted。
5. skipped verifier 不等于 pass。
6. failed/error verifier 必须阻塞对应 promotion。
7. accepted artifact 不得依赖 draft/private artifact。
8. public KB 不得依赖 private KB。
9. private KB 可以依赖 public accepted artifact。
10. public KB 不得包含 private conjecture、unpublished idea、未经审核的 LLM 输出。
```

### 4.2 存储与索引

```text
1. YAML artifact 是唯一 source of truth。
2. SQLite index、manifest、embedding index、weight store、retrieval cache 都是可重建 sidecar。
3. sidecar 不得成为人工编辑的事实源。
4. 所有 generated outputs 必须 deterministic，除非明确标注为 experimental cache。
5. .cosheaf/ 下的 runtime 输出默认不得进入 Git。
6. provider logs、MCP traces、context previews 默认进入 .cosheaf/ 或 configured output dir。
```

### 4.3 Agent / MCP / API 权限

```text
1. MCP read-only tools 可默认开启。
2. MCP write tools 必须显式 allow-write。
3. MCP 不暴露 arbitrary shell。
4. MCP 不暴露 direct promote / write accepted。
5. Hosted API worker 只能返回 WorkerBundle、typed sub-result、draft proposal。
6. External agent 不得直接改 accepted path。
7. Internal orchestrator 不得绕过 reducer/gate/review。
8. Model output 必须保留 failure、uncertainty、citations、risk_flags。
9. Provider call 必须可取消、可超时、可审计。
10. Skill 不能扩大 agent 权限。
```

### 4.4 Public / private 数据边界

```text
1. public task 默认只能读 public KB。
2. private task 可以读 private + public，但输出不得泄露到 public KB。
3. hosted provider 使用 private KB 前必须显式 policy_mode=private_research。
4. MCP resource URI 必须带 root/scope 信息。
5. retrieval score 不能绕过 policy filter。
6. context preview 必须显示将发送给 provider 的 root/scope 摘要。
7. public KB readonly root 不能被 MCP/API/worker 修改。
```

### 4.5 外部工具不变量

```text
1. MarkItDown 只能作为 opt-in source-ingestion adapter，不得进入 validation/gate/promotion truth path。
2. MarkItDown 输出只能进入 source-note staging、draft proposal 或 .cosheaf/ingest。
3. MarkItDown 默认禁 URL、插件、OCR、LLM vision、Azure Document Intelligence。
4. Headroom 只能作为 noncanonical view/log/chunk 压缩实验，默认关闭。
5. Headroom 不得改写 YAML、accepted KB、gate input、retrieval score input、AGENTS.md、CODEX_WORKFLOW。
6. CodeGraph 只能是 dev-only 代码理解/影响面分析工具，不得成为 runtime dependency。
7. Understand-Anything 只能是隔离人工 onboarding / architecture visualization 工具。
8. 外部工具缺失不得阻塞核心 validate/gate/test，除非该 Task 是工具专项测试。
```

---

## 5. 每个 Task 开始前必须读取

```text
tcs-cosheaf:
  AGENTS.md
  README.md
  docs/ARCHITECTURE.md
  docs/ROADMAP.md
  docs/CODEX_WORKFLOW.md
  docs/GATES.md
  docs/ARTIFACT_SCHEMA.md
  docs/AGENT_ACCESS.md if present
  docs/MCP_SERVER.md if present
  docs/AGENT_PROVIDERS.md if present
  context/PROJECT_STATE.md
  context/INTERFACE_REGISTRY.md
  context/CURRENT_MILESTONE.md
  pyproject.toml
  Makefile
  .github/workflows/
  cosheaf/
  schemas/
  tests/

tcs-cosheaf-workspace-template:
  AGENTS.md
  README.md
  cosheaf.toml
  docs/PUBLIC_KB_SETUP.md
  QUICKSTART.md or docs/QUICKSTART.md
  Makefile
  scripts/
  .github/workflows/

tcs-kb-public:
  AGENTS.md
  README.md
  docs/
  kb/public/
  context/
  .github/workflows/
```

若文件不存在：

```text
1. 不得假设内容。
2. 在状态审计中记录缺失。
3. 只在 Task 范围允许时创建或修复。
```

---

## 6. PR 工作协议

每个 PR 必须满足：

```text
1. branch 名称使用：
   <phase-task>-short-description
   禁止使用 `codex/`、`codex-` 或任何 Codex 专属前缀。

2. PR 描述必须包含：
   - Goal
   - Scope
   - Files changed
   - Tests run
   - Commands unavailable
   - Invariants checked
   - Security/privacy impact
   - Known limitations
   - Follow-up tasks

3. 每个 public interface change 必须更新：
   context/INTERFACE_REGISTRY.md

4. 每个架构决策必须新增或更新：
   docs/ADR/*.md

5. 每个行为变化必须有测试。
6. 每个 CLI 行为必须有 smoke test。
7. 每个 MCP tool 必须有 allow/deny 测试。
8. 每个 gate 行为必须有 pass/fail 测试。
9. 每个权限边界必须有 negative test。
10. 每个 provider 行为必须有 fake/mocked provider 测试。
```

每次结束前至少尝试运行：

```bash
make lint
make typecheck
make test
make validate
make gate
```

如果某个仓库没有对应命令，必须报告：

```text
command missing: <command>
reason:
whether this PR should add it:
```

不得把“命令不存在”写成“通过”。

---

## 7. 目标架构

### 7.1 分层

```text
Knowledge Layer
  artifact YAML
  issue YAML
  review YAML
  source note
  formalization metadata

Storage / Index Layer
  loader
  validator
  deterministic manifest
  SQLite index
  dependency graph
  rebuildable sidecars

Memory / Retrieval Layer
  librarian
  artifact cards
  hybrid retrieval
  graph weights
  personalized PageRank
  retrieval audit log

Context Layer
  bounded context pack v2
  role-specific context
  hot / warm / cold memory split
  context preview for provider calls

Service Layer
  WorkspaceService
  ValidationService
  GateService
  MemorySearchService
  ContextPackService
  TaskService
  BundleValidationService
  DraftWriteService
  ProviderCallService

Agent Access Layer
  MCP resources
  MCP prompts
  MCP read-only tools
  MCP controlled-write tools
  optional Skill package
  CLI fallback

Agent Orchestration Layer
  external-agent orchestrator mode
  internal orchestrator state machine
  task DAG
  worker dispatch
  reducer
  run record

Worker Runtime Layer
  local command worker
  fake provider worker
  hosted API worker
  role-specific worker contracts
  structured WorkerBundle

Provider Gateway Layer
  fake provider
  OpenAI-compatible transport
  future Anthropic/Gemini/local transports
  capability negotiation
  secret redaction
  cost/latency/run logging

Verification Layer
  Python checker
  SAT adapter
  SMT adapter
  Lean local file checker
  Lean external library ref checker

Gate / Review / Promotion Layer
  schema gate
  dependency gate
  source gate
  verifier gate
  formal link gate
  PR checklist gate
  human review
  promotion workflow

Evaluation / Observability Layer
  retrieval eval
  context eval
  MCP eval
  provider security eval
  agent dry-run eval
  structured run logs
  optional OpenTelemetry

Developer Tooling Layer
  optional CodeGraph local code index
  optional Understand-Anything isolated dashboard
  optional Headroom noncanonical compression experiment
  no source-of-truth authority
```

### 7.2 依赖方向

```text
core
  -> storage
  -> graph
  -> memory / retrieval
  -> context
  -> verification
  -> gates
  -> services
  -> agent
  -> mcp
  -> cli
```

允许：

```text
cli -> services
mcp -> services
agent/orchestrator -> services
provider gateway -> agent/service models
workspace-template -> tcs-cosheaf CLI/MCP/API
```

禁止：

```text
core importing cli
storage importing agent
memory importing hosted provider
mcp shelling out arbitrary commands
mcp bypassing services
provider gateway importing gates in a way that creates circular dependency
gates requiring network
verification requiring network by default
public KB importing workspace private data
```

---

## 8. 分阶段路线总览

```text
Phase R: 回退审计与方向修正
Phase A: Agent Access Service Layer 与公共 schema
Phase M: MCP Server
Phase P: Hosted Model API Provider 与 hosted workers
Phase K: Skill / Operator Package
Phase W: Workspace-template integration
Phase E: Evaluation / Security hardening
Phase V: v0.2.1 release candidate
```

执行顺序不可跳过。每个 Phase 内按 Task 顺序执行。

---

# Phase R: 回退审计与方向修正

目标：以 `v0.2.0 / 9b1c3fa` 为基线，审计 post-v0.2.0 变化，清除 local-only roadmap 污染，并把当前计划落库。

## Task R.1: v0.2.0 基线审计与定向回退报告

```text
Repository:
  tcs-cosheaf

Branch:
  rollback-audit-v020

Goal:
  Compare current main with v0.2.0 tag and decide exact revert/rewrite scope.

Read first:
  AGENTS.md
  README.md
  docs/ROADMAP.md
  context/CURRENT_MILESTONE.md
  context/PROJECT_STATE.md
  pyproject.toml
  cosheaf/
  tests/

Required commands:
  git fetch --tags
  git log --oneline v0.2.0..main
  git diff --name-status v0.2.0..main
  git diff --stat v0.2.0..main

Create or update only:
  docs/POST_V020_ROLLBACK_AUDIT.md

Must classify each changed file:
  KEEP
  REVERT
  REWRITE
  NEEDS_HUMAN_DECISION

Classification rules:
  KEEP:
    working code/docs compatible with API/MCP/Skill direction.
  REVERT:
    changes that make local-only policy permanent or break invariants.
  REWRITE:
    docs/issues/milestones whose direction is wrong but content can be reused.
  NEEDS_HUMAN_DECISION:
    ambiguous provider/security/license/schema changes.

Rules:
  1. Do not implement new features.
  2. Do not reset main.
  3. Do not change accepted KB.
  4. Baseline is v0.2.0 / 9b1c3fa, not v0.1.1.
  5. Any local-only roadmap language must be flagged REWRITE.
  6. Any “hosted provider is out of scope forever” language must be flagged REWRITE.

Before finishing:
  - run available docs/test commands if safe
  - record unavailable commands honestly
  - stop
```

Acceptance criteria:

```text
1. Audit names exact commits after v0.2.0.
2. Audit identifies local-only roadmap pollution.
3. Audit identifies files safe to keep.
4. No runtime behavior changed.
5. No KB artifacts changed.
```

---

## Task R.2: Rewrite milestone and roadmap toward API/MCP/Skill

```text
Repository:
  tcs-cosheaf

Branch:
  roadmap-agent-api-mcp

Goal:
  Replace local-only next-focus docs with v0.2.1 Agent Access + Hosted API milestone.

Read first:
  docs/POST_V020_ROLLBACK_AUDIT.md
  context/CURRENT_MILESTONE.md
  docs/ROADMAP.md
  README.md
  docs/ARCHITECTURE.md

Allowed changes:
  context/CURRENT_MILESTONE.md
  docs/ROADMAP.md
  docs/ADR/00xx-agent-api-mcp-direction.md
  docs/CODEX_DEVELOPMENT_PLAN.md or docs/CODEX_DEVELOPMENT_PLAN_V3.md
  context/INTERFACE_REGISTRY.md if public interfaces are named

Required content:
  1. MCP first-class interface.
  2. Skill as operator guide.
  3. Hosted model API as scheduled capability.
  4. Local-only mode as fallback/testing mode only.
  5. External agent can be orchestrator or worker.
  6. Internal orchestrator may call hosted API workers when policy permits.
  7. v0.2.0 remains baseline; v0.2.1 targets agent access + provider gateway.

Rules:
  1. Do not change application code.
  2. Do not change schemas.
  3. Do not change KB artifacts.
  4. Do not overclaim production readiness.
```

Acceptance criteria:

```text
1. Roadmap no longer says next focus is only local orchestrator hardening.
2. API provider integration is scheduled, not deferred indefinitely.
3. Docs preserve gate/review/promotion boundaries.
4. The plan states that real API is supported by design but not used in CI.
```

---

## Task R.3: Install longplan v3 as current repo plan

```text
Repository:
  tcs-cosheaf

Branch:
  install-longplan-v3

Goal:
  Add this longplan v3 as the current durable Codex execution plan.

Read first:
  docs/POST_V020_ROLLBACK_AUDIT.md
  docs/ROADMAP.md
  context/CURRENT_MILESTONE.md
  docs/CODEX_DEVELOPMENT_PLAN.md if present

Allowed changes:
  docs/CODEX_DEVELOPMENT_PLAN_V3.md
  docs/CODEX_DEVELOPMENT_PLAN.md only to point to v3 or mark old plan historical
  context/CURRENT_MILESTONE.md

Rules:
  1. Do not implement MCP/provider code.
  2. Do not remove old plan unless maintainer explicitly requested.
  3. Mark old local-only plan as historical if it conflicts with v3.
  4. Stop after docs update.
```

Acceptance criteria:

```text
1. Repo has a single current execution plan.
2. Conflicting old plan is clearly historical or superseded.
3. No code changed.
```

---

# Phase A: Agent Access Service Layer 与公共 schema

目标：先抽 service layer 和 typed schemas，使 CLI、MCP、internal orchestrator、hosted API workers 共用同一安全入口。

## Task A.1: Agent access ADR and threat model

```text
Repository:
  tcs-cosheaf

Branch:
  agent-access-adr-threat-model

Goal:
  Record the durable architecture for MCP + Skill + hosted API before code changes.

Read first:
  docs/CODEX_DEVELOPMENT_PLAN_V3.md or current plan
  docs/ARCHITECTURE.md
  docs/GATES.md
  docs/ARTIFACT_SCHEMA.md
  context/PROJECT_STATE.md

Allowed changes:
  docs/AGENT_ACCESS.md
  docs/ADR/00xx-agent-access-architecture.md
  docs/SECURITY.md if present
  context/INTERFACE_REGISTRY.md if public names are introduced

Required decisions:
  1. MCP is the primary external-agent machine interface.
  2. Skill is an optional operator guide.
  3. Hosted API provider is a planned core worker capability.
  4. CLI remains human/CI oracle.
  5. Service layer is shared by CLI/MCP/orchestrator/provider workers.
  6. Controlled writes are draft/proposal/bundle only.
  7. Accepted promotion remains outside agent authority.

Do not implement code.
```

Acceptance criteria:

```text
1. Agent access architecture is documented.
2. Threat model covers MCP, provider, Skill, external agent and private KB leakage.
3. No runtime behavior changed.
```

---

## Task A.2: Extract service layer from CLI

```text
Repository:
  tcs-cosheaf

Branch:
  service-layer-cli-mcp-api

Goal:
  Create typed service functions so CLI, MCP server, and internal orchestrator/API workers do not duplicate logic or shell out to each other.

Read first:
  cosheaf/cli.py or CLI modules
  cosheaf/memory/
  cosheaf/gates/
  cosheaf/agent/
  tests/
  context/INTERFACE_REGISTRY.md

Allowed changes:
  cosheaf/services/
  cosheaf/cli.py or CLI modules
  tests/
  docs/ARCHITECTURE.md
  context/INTERFACE_REGISTRY.md

Required services:
  WorkspaceService
  ValidationService
  GateService
  MemorySearchService
  ContextPackService
  TaskService
  BundleValidationService
  DraftWriteService

Rules:
  1. CLI must call services.
  2. No MCP implementation in this task.
  3. No hosted API call in this task.
  4. Services must return typed results, not only Rich terminal text.
  5. Existing CLI behavior must remain backward compatible.
  6. No accepted writes.
  7. No network.

Before finishing:
  - service unit tests
  - CLI regression tests
  - run make lint/typecheck/test/validate/gate if available
  - stop
```

Acceptance criteria:

```text
1. Existing CLI tests pass.
2. Service unit tests exist.
3. No public behavior regression.
4. New service interfaces are registered.
```

---

## Task A.3: Define public interface schemas for agent access

```text
Repository:
  tcs-cosheaf

Branch:
  agent-access-schemas

Goal:
  Define stable request/response schemas for MCP and hosted model workers.

Allowed changes:
  schemas/agent_access/
  cosheaf/services/models.py or equivalent
  tests/
  docs/AGENT_ACCESS.md
  context/INTERFACE_REGISTRY.md

Required schemas:
  WorkspaceInfoResult
  ValidateResult
  GateRunResult
  MemorySearchRequest
  MemorySearchResult
  ContextBuildRequest
  ContextBuildResult
  CreateTaskRequest
  CreateTaskResult
  WorkerBundleSubmitRequest
  WorkerBundleSubmitResult
  DraftArtifactWriteRequest
  DraftArtifactWriteResult
  ModelCallRequest
  ModelCallResult
  ProviderRunRecord
  ErrorResult

Rules:
  1. Do not expose internal Python objects directly.
  2. Every error result must have code, message, remediation, and blocking flag.
  3. Include public/private policy fields.
  4. Include consent fields for provider-send flows.
  5. Schema additions must be backward-compatible or explicitly versioned.
```

Acceptance criteria:

```text
1. JSON schema or serialization tests pass.
2. Public/private fields are present.
3. Interface registry updated.
4. Backward compatibility risks documented.
```

---

## Task A.4: Context send policy and provider preview

```text
Repository:
  tcs-cosheaf

Branch:
  context-send-policy-preview

Goal:
  Add a policy service that determines what context may be shown to external agents or sent to hosted providers.

Allowed changes:
  cosheaf/services/
  cosheaf/context/ or cosheaf/agent/context modules if needed
  tests/
  docs/AGENT_ACCESS.md
  docs/SECURITY.md if present
  context/INTERFACE_REGISTRY.md

Required behavior:
  1. public task can only include public KB by default.
  2. private task can include private + public only with policy_mode=private_research.
  3. provider send preview lists issue id, artifact ids, root scopes, estimated tokens, and risk flags.
  4. preview must not include API key or secrets.
  5. policy denial returns structured ErrorResult.

Rules:
  1. No actual provider call in this task.
  2. No MCP implementation in this task.
  3. Tests must cover private leakage denial.
```

Acceptance criteria:

```text
1. Provider context preview exists.
2. Public/private policy tests exist.
3. Retrieval score cannot bypass scope filter.
```

---

# Phase M: MCP Server

目标：让主流 agent 可以通过标准 MCP 接口调用 Cosheaf。MCP v1 先 read-only，再 controlled write；绝不暴露 arbitrary shell 或 direct promotion。

## Task M.1: MCP design ADR and security model

```text
Repository:
  tcs-cosheaf

Branch:
  mcp-design-security

Goal:
  Document the MCP server boundary before implementation.

Read first:
  docs/AGENT_ACCESS.md
  docs/ARCHITECTURE.md
  docs/GATES.md
  context/INTERFACE_REGISTRY.md

Allowed changes:
  docs/MCP_SERVER.md
  docs/ADR/00xx-mcp-agent-interface.md
  docs/SECURITY.md if present
  context/INTERFACE_REGISTRY.md

Required decisions:
  1. MCP resources expose context/data, not authority.
  2. MCP tools are whitelisted service calls, not shell.
  3. MCP prompts are workflow templates.
  4. Human confirmation or server allow-write flag required for controlled writes.
  5. Direct promote/write accepted remains forbidden.
  6. Tool outputs must use structured content where possible.
  7. Private KB exposure requires policy_mode and configured root allowlist.
  8. MCP server must have stdio mode first.

Do not implement code.
```

Acceptance criteria:

```text
1. MCP threat model exists.
2. Read/write tool taxonomy exists.
3. Forbidden tool list exists.
4. No runtime behavior changed.
```

---

## Task M.2: Read-only MCP server v1

```text
Repository:
  tcs-cosheaf

Branch:
  mcp-readonly-server

Goal:
  Add a local MCP server exposing safe read-only Cosheaf tools and resources.

Allowed changes:
  cosheaf/mcp/
  cosheaf/cli.py or entrypoint config
  pyproject.toml optional extra if needed
  tests/
  docs/MCP_SERVER.md
  context/INTERFACE_REGISTRY.md

Required CLI:
  cosheaf mcp serve --stdio
  cosheaf mcp list-tools

Read-only tools:
  workspace_info
  validate
  gate_run
  memory_search
  context_build
  context_show
  orchestrator_plan

Resources:
  cosheaf://workspace
  cosheaf://issues/{issue_id}
  cosheaf://artifacts/{artifact_id}/card
  cosheaf://context/{issue_id}
  cosheaf://gate/latest

Rules:
  1. No arbitrary shell.
  2. No draft write in this task.
  3. No accepted write.
  4. No hosted provider call.
  5. Must call service layer, not shell out to CLI.
  6. Tests use fake MCP client or protocol-level call fixtures.
```

Acceptance criteria:

```text
1. MCP server starts over stdio.
2. tools/list returns whitelisted tools only.
3. tools/call returns structured results.
4. resource reads respect scope.
5. Existing CLI/tests still pass.
```

---

## Task M.3: MCP prompts and resources hardening

```text
Repository:
  tcs-cosheaf

Branch:
  mcp-prompts-resources

Goal:
  Add MCP prompts and resource templates that guide agents without expanding authority.

Allowed changes:
  cosheaf/mcp/
  tests/
  docs/MCP_SERVER.md
  docs/AGENT_ACCESS.md
  context/INTERFACE_REGISTRY.md

Required prompts:
  start_issue_work
  reason_about_issue
  verify_draft
  prepare_review_bundle
  public_kb_contribution_check

Prompt rules:
  1. Must include accepted/draft distinction.
  2. Must tell agent to use artifact ids.
  3. Must forbid writing accepted knowledge.
  4. Must instruct final validate/gate/test.
  5. Must not include private KB content in prompt templates.

Resource rules:
  1. Resource URI must include scope where needed.
  2. Private resources require explicit policy permission.
```

Acceptance criteria:

```text
1. Prompts are listed through MCP.
2. Prompts are governance-safe.
3. Private resources cannot be read from public mode.
```

---

## Task M.4: Controlled-write MCP tools

```text
Repository:
  tcs-cosheaf

Branch:
  mcp-controlled-write-tools

Goal:
  Allow external agents to write draft/proposal artifacts through safe services.

Allowed changes:
  cosheaf/mcp/
  cosheaf/services/
  tests/
  docs/MCP_SERVER.md
  context/INTERFACE_REGISTRY.md

Controlled-write tools:
  write_draft_artifact
  write_worker_bundle
  write_review_request
  write_source_note_draft
  submit_worker_bundle

Rules:
  1. Must require --allow-write server flag or equivalent config.
  2. Must reject kb/accepted/ paths.
  3. Must reject readonly public root writes.
  4. Must reject public KB writes unless explicit allow-public-draft and root is writable.
  5. Must run schema validation after write.
  6. Must return paths and validation result.
  7. No promotion tool in v1.
  8. No arbitrary file write.
```

Acceptance criteria:

```text
1. Draft writes work through MCP.
2. Accepted writes are rejected by tests.
3. Private/public leakage tests exist.
4. Schema validation runs after write.
```

---

## Task M.5: MCP end-to-end smoke with fake client

```text
Repository:
  tcs-cosheaf

Branch:
  mcp-e2e-smoke

Goal:
  Add a deterministic MCP smoke flow that simulates an external agent.

Allowed changes:
  tests/mcp/
  examples/mcp/
  docs/MCP_SERVER.md

Flow:
  1. Start MCP server over stdio.
  2. Call workspace_info.
  3. Call memory_search.
  4. Call context_build.
  5. With allow-write, write worker bundle draft.
  6. Run validate.
  7. Run gate_run.

Rules:
  1. No real model.
  2. No hosted provider.
  3. No accepted writes.
  4. Deterministic fixture only.
```

Acceptance criteria:

```text
1. MCP smoke test runs in CI.
2. It exercises read-only and controlled-write modes.
3. Public/private boundaries are tested.
```

---

# Phase P: Hosted Model API Provider 与 hosted workers

目标：把 API 调用作为一等能力加入 Cosheaf，但必须保持 fake provider 测试、secret redaction、policy-filtered context、no accepted promotion。

## Task P.1: Provider gateway design ADR

```text
Repository:
  tcs-cosheaf

Branch:
  provider-gateway-design

Goal:
  Define hosted model API calling as first-class, scheduled capability.

Read first:
  docs/AGENT_ACCESS.md
  docs/ARCHITECTURE.md
  docs/SECURITY.md if present
  cosheaf/agent/model_provider.py if present

Allowed changes:
  docs/AGENT_PROVIDERS.md
  docs/ADR/00xx-hosted-provider-gateway.md
  docs/SECURITY.md if present
  context/INTERFACE_REGISTRY.md

Required decisions:
  1. Hosted API calls are planned and supported, not rejected.
  2. Local-only is fallback/testing mode, not product boundary.
  3. Provider gateway abstracts OpenAI-compatible and future providers.
  4. Fake provider remains required for tests.
  5. Private KB policy controls what can be sent.
  6. API outputs can only create WorkerBundle/proposal/draft, never accepted.
  7. Logs must redact secrets and record cost/latency/model/provider metadata.
  8. Real provider calls require explicit config and explicit consent.

Do not implement runtime code.
```

Acceptance criteria:

```text
1. ADR explicitly reverses local-only framing.
2. Security and data policy are documented.
3. No runtime code yet.
```

---

## Task P.2: Provider gateway core with fake + OpenAI-compatible transport

```text
Repository:
  tcs-cosheaf

Branch:
  provider-gateway-core

Goal:
  Implement provider-neutral hosted API gateway with fake transport and optional OpenAI-compatible transport.

Allowed changes:
  cosheaf/agent/providers/
  cosheaf/agent/model_provider.py or equivalent
  cosheaf/services/model_calls.py
  tests/providers/
  docs/AGENT_PROVIDERS.md
  pyproject.toml only for optional extras
  context/INTERFACE_REGISTRY.md

Required models:
  ModelRequest
  ModelResponse
  ProviderConfig
  ProviderCapability
  ProviderRunRecord
  ProviderError

Required provider modes:
  fake
  openai_compatible

Rules:
  1. Tests must not call real network.
  2. Real API requires explicit config and API key.
  3. Secrets must never be logged.
  4. Timeout, retry, cancellation, and rate-limit handling must exist.
  5. Structured output schema validation required for WorkerBundle outputs.
  6. Unsupported parameters must be dropped or reported through capability negotiation.
  7. No default provider may send data externally.
```

Acceptance criteria:

```text
1. Fake provider tests pass.
2. Mocked OpenAI-compatible transport tests pass.
3. No API key needed in CI.
4. Run records are written and redacted.
5. Capability negotiation is tested.
```

---

## Task P.3: Role-specific hosted worker contracts

```text
Repository:
  tcs-cosheaf

Branch:
  hosted-worker-role-contracts

Goal:
  Define role-specific hosted worker contracts before dispatch integration.

Allowed changes:
  cosheaf/agent/roles/
  cosheaf/agent/workers/
  tests/
  docs/AGENT_ROLES.md
  context/INTERFACE_REGISTRY.md

Required roles:
  reasoner
  verifier
  counterexampleer
  explorer
  formalizer
  librarian_summarizer

Each role must define:
  allowed inputs
  forbidden actions
  output schema
  context policy
  provider capability requirements
  stop conditions
  risk flags

Rules:
  1. Do not make all workers share one generic prompt.
  2. Hosted worker output must be WorkerBundle v2 or typed sub-result.
  3. Verifier role cannot mark accepted or human_reviewed.
  4. Reasoner cannot mark conjecture as theorem.
  5. Formalizer cannot claim semantic alignment without human alignment review.
  6. All tests use fake provider.
```

Acceptance criteria:

```text
1. Role contracts are machine-readable.
2. Forbidden actions are explicit.
3. Fake hosted worker can produce valid bundle.
4. Invalid provider output is rejected.
```

---

## Task P.4: Hosted worker execution service

```text
Repository:
  tcs-cosheaf

Branch:
  hosted-worker-execution-service

Goal:
  Connect provider gateway to role-specific hosted workers without orchestrator dispatch yet.

Allowed changes:
  cosheaf/agent/workers/
  cosheaf/services/
  tests/providers/
  tests/agent/
  docs/AGENT_PROVIDERS.md
  context/INTERFACE_REGISTRY.md

Required behavior:
  1. Build ModelRequest from WorkerTask + context policy.
  2. Show provider send preview.
  3. Execute fake provider in tests.
  4. Parse/validate WorkerBundle output.
  5. Record ProviderRunRecord.
  6. Return rejected result for malformed output.

Rules:
  1. No real API in CI.
  2. No accepted writes.
  3. No direct promotion.
  4. Provider send preview required before real provider.
```

Acceptance criteria:

```text
1. Fake hosted worker path works.
2. Malformed model output is rejected.
3. Provider run record redacts secrets.
4. Private context cannot be sent without policy permission.
```

---

## Task P.5: Internal orchestrator dispatch to hosted API workers

```text
Repository:
  tcs-cosheaf

Branch:
  orchestrator-hosted-worker-dispatch

Goal:
  Allow Cosheaf internal orchestrator to dispatch tasks to hosted API workers when explicitly configured.

Allowed changes:
  cosheaf/agent/orchestrator_runner.py
  cosheaf/agent/orchestrator_planner.py
  cosheaf/services/
  tests/agent/
  tests/providers/
  docs/ARCHITECTURE.md
  docs/AGENT_PROVIDERS.md

Required CLI:
  cosheaf orchestrator run --issue <issue-id> --provider fake
  cosheaf orchestrator run --issue <issue-id> --provider openai-compatible --confirm-send

Rules:
  1. Default provider is fake or disabled, but real provider support must exist.
  2. Real provider requires explicit --confirm-send or config approval.
  3. Must show which KB roots/context will be sent before call.
  4. Must support public-only mode.
  5. Must write provider run records.
  6. Must validate returned bundle before reducer.
  7. No accepted writes.
  8. No real provider calls in CI.
```

Acceptance criteria:

```text
1. Fake end-to-end hosted-worker path passes.
2. Real provider path is configurable but not run in CI.
3. Context-preview and consent tests exist.
4. Reducer/gate/review boundaries remain intact.
```

---

## Task P.6: Provider configuration and secret handling docs

```text
Repository:
  tcs-cosheaf

Branch:
  provider-config-secret-docs

Goal:
  Document safe configuration for real API providers.

Allowed changes:
  docs/AGENT_PROVIDERS.md
  docs/SECURITY.md if present
  .env.example only if project already uses env examples
  tests/ if redaction docs include examples

Required content:
  1. Environment variable names.
  2. No API keys in repo.
  3. No API keys in logs.
  4. How to run fake provider.
  5. How to run real provider manually.
  6. How to restrict private KB sending.
  7. How to inspect provider run records.

Rules:
  1. Do not add real keys.
  2. Do not enable real provider by default.
  3. Do not change CI to require provider secrets.
```

Acceptance criteria:

```text
1. A user can configure provider manually.
2. CI remains secret-free.
3. Security warnings are explicit.
```

---

# Phase K: Skill / Operator Package

目标：提供可安装/可复制的 operator Skill，使 ChatGPT/Codex-like agent 知道如何通过 MCP/CLI/API 安全操作 Cosheaf。Skill 不替代 MCP，不扩大权限。

## Task K.1: Cosheaf operator Skill package

```text
Repository:
  tcs-cosheaf

Branch:
  cosheaf-operator-skill

Goal:
  Add an optional Skill package that teaches ChatGPT/Codex-like agents how to operate Cosheaf through MCP/CLI/API safely.

Allowed changes:
  skills/cosheaf-operator/SKILL.md
  skills/cosheaf-operator/agents/openai.yaml
  skills/cosheaf-operator/references/
  docs/AGENT_ACCESS.md
  tests/skill validation if available

Skill must cover:
  1. When to use Cosheaf.
  2. Files to read first.
  3. Preferred path: MCP tools.
  4. Fallback path: CLI commands.
  5. Hosted provider policy.
  6. Forbidden actions.
  7. WorkerBundle output discipline.
  8. PR summary format.
  9. Public/private safety.
  10. No accepted writes.

Rules:
  1. Skill is instructions, not source of truth.
  2. Skill must not include private KB content.
  3. Skill must not tell agent to bypass MCP/service/gate.
  4. Skill must be concise and progressive-load friendly.
```

Acceptance criteria:

```text
1. Skill validates structurally if validator exists.
2. Skill references MCP tools and CLI fallback.
3. Skill is concise enough to be usable.
4. Skill cannot be interpreted as granting accepted-write authority.
```

---

## Task K.2: Skill usage examples and safety tests

```text
Repository:
  tcs-cosheaf

Branch:
  cosheaf-skill-examples

Goal:
  Add examples showing how an agent should use the Skill without weakening governance.

Allowed changes:
  skills/cosheaf-operator/references/examples.md
  docs/AGENT_ACCESS.md
  tests/skill validation if available

Examples:
  1. Read-only investigation.
  2. Write draft artifact.
  3. Submit worker bundle.
  4. Refuse accepted-write request.
  5. Run hosted fake provider path.

Rules:
  1. Examples must not include private data.
  2. Examples must not include real API keys.
  3. Examples must end with validate/gate/test.
```

Acceptance criteria:

```text
1. Examples are actionable.
2. Forbidden action examples are clear.
3. Skill remains optional.
```

---

# Phase W: Workspace-template integration

目标：让 workspace-template 成为运行 MCP server、fake provider demo、real provider config 的默认入口。

## Task W.1: Workspace MCP/API quickstart

```text
Repository:
  tcs-cosheaf-workspace-template

Branch:
  workspace-agent-access-quickstart

Goal:
  Make workspace-template the default place to run MCP server and hosted worker experiments.

Read first:
  README.md
  QUICKSTART.md or docs/QUICKSTART.md
  cosheaf.toml
  Makefile
  docs/PUBLIC_KB_SETUP.md

Allowed changes:
  README.md
  QUICKSTART.md or docs/QUICKSTART.md
  Makefile
  scripts/
  docs/AGENT_ACCESS.md
  .env.example

Required commands:
  make mcp-serve
  make mcp-smoke
  make provider-fake-smoke
  make provider-config-check

Rules:
  1. No real API key in repo.
  2. .env.example only names variables.
  3. Public KB remains readonly.
  4. Demo must not write accepted artifacts.
  5. Real provider enablement must be documented as manual opt-in.
```

Acceptance criteria:

```text
1. New user can start MCP server from workspace.
2. Fake provider demo runs locally.
3. Docs explain how to enable real provider safely.
4. Public/private boundary preserved.
```

---

## Task W.2: End-to-end external agent demo

```text
Repository:
  tcs-cosheaf-workspace-template

Branch:
  external-agent-e2e-demo

Goal:
  Demonstrate an external agent using MCP to search context, write draft, validate bundle, and run gates.

Allowed changes:
  examples/agent_demo/
  scripts/demo_agent_mcp.py
  README.md
  docs/AGENT_ACCESS.md
  tests/ if present

Demo flow:
  1. Start MCP server.
  2. Call workspace_info.
  3. Call memory_search.
  4. Call context_build.
  5. Write draft artifact.
  6. Write worker bundle.
  7. Run validate and gate.

Rules:
  1. Use fake client or scripted MCP calls.
  2. No hosted API required.
  3. No accepted writes.
  4. No public KB writes.
```

Acceptance criteria:

```text
1. Demo is reproducible.
2. Agent path exercises MCP, not direct shell.
3. Public/private boundary preserved.
```

---

## Task W.3: End-to-end hosted worker demo with fake provider

```text
Repository:
  tcs-cosheaf-workspace-template

Branch:
  hosted-worker-fake-demo

Goal:
  Demonstrate internal orchestrator dispatch to hosted-style workers using fake provider.

Allowed changes:
  examples/hosted_worker_demo/
  scripts/demo_hosted_worker_fake.py
  Makefile
  README.md
  docs/AGENT_ACCESS.md

Demo flow:
  1. Build context for demo issue.
  2. Run orchestrator with provider=fake.
  3. Produce WorkerBundle.
  4. Validate bundle.
  5. Run gate.

Rules:
  1. No real API call.
  2. No accepted writes.
  3. Demo must explain how real provider differs.
```

Acceptance criteria:

```text
1. Fake hosted-worker demo runs locally.
2. It exercises provider gateway path.
3. It does not require secrets.
```

---

# Phase E: Evaluation / Security hardening

目标：保证 MCP、provider、Skill、external-agent workflows 有回归测试和安全负例，避免 agent access 削弱知识治理。

## Task E.1: Agent access security regression suite

```text
Repository:
  tcs-cosheaf

Branch:
  agent-access-security-regression

Goal:
  Add negative tests for MCP, hosted API workers, and external-agent workflows.

Allowed changes:
  tests/security/
  tests/mcp/
  tests/providers/
  docs/SECURITY.md
  docs/AGENT_ACCESS.md

Must test:
  1. MCP cannot write accepted.
  2. MCP cannot access private KB from public mode.
  3. Hosted provider cannot receive private context without policy permission.
  4. Provider logs redact secrets.
  5. Malformed model output rejected.
  6. Tool descriptions/prompts cannot override governance rules.
  7. Promotion remains CLI/human-review gated.
  8. Skill cannot override repository invariants.

Rules:
  1. No real provider calls.
  2. No secrets.
  3. No accepted writes.
```

Acceptance criteria:

```text
1. All negative tests pass after guard implementation.
2. Security docs map each test to a threat.
3. CI includes the suite.
```

---

## Task E.2: MCP/provider eval harness

```text
Repository:
  tcs-cosheaf

Branch:
  agent-access-eval-harness

Goal:
  Add deterministic evals for MCP and provider-worker paths.

Allowed changes:
  evals/
  cosheaf/evals/
  tests/
  docs/EVALUATION.md
  context/INTERFACE_REGISTRY.md

Required evals:
  mcp_tool_smoke
  mcp_private_leakage
  provider_bundle_validity
  provider_malformed_output_rejection
  context_preview_accuracy
  agent_draft_write_safety

Metrics:
  pass_count
  blocking_failure_count
  private_leakage_count
  accepted_write_attempt_blocked
  invalid_bundle_rejection_count
  required_artifact_hit

Rules:
  1. No real model.
  2. No network.
  3. Deterministic fixtures only.
```

Acceptance criteria:

```text
1. Evals can run in CI.
2. Metrics are machine-readable.
3. Security regressions are visible.
```

---

## Task E.3: Structured run logging for MCP and provider calls

```text
Repository:
  tcs-cosheaf

Branch:
  agent-access-run-logging

Goal:
  Ensure MCP and provider flows are auditable.

Allowed changes:
  cosheaf/observability/ or cosheaf/logging/
  cosheaf/mcp/
  cosheaf/agent/providers/
  tests/
  docs/OBSERVABILITY.md
  context/INTERFACE_REGISTRY.md

Required run log fields:
  run_id
  issue_id
  tool_name or worker_role
  provider
  model
  root_scopes
  artifact_ids
  prompt_hash
  output_hash
  cost_estimate
  latency_ms
  status
  error_code
  redaction_applied
  started_at
  ended_at

Rules:
  1. Logs must not include API keys.
  2. Logs must not include hidden chain-of-thought.
  3. Logs must not dump full private KB by default.
  4. Logs must be machine-readable JSON/YAML.
```

Acceptance criteria:

```text
1. MCP tool calls are logged.
2. Provider calls are logged.
3. Secret redaction tests pass.
```

---

# Phase V: v0.2.1 Release Candidate

目标：收口为 v0.2.1 Agent Access + Hosted API Provider release candidate。必须保守陈述，不夸大生产能力。

## Task V.1: Three-repo compatibility audit

```text
Repository:
  Start from tcs-cosheaf, inspect workspace-template and public KB.

Branch:
  v021-three-repo-compat-audit

Goal:
  Verify that v0.2.1 agent access changes work across all three repos.

Read first:
  tcs-cosheaf README, pyproject, docs, tests
  workspace-template README, Makefile, cosheaf.toml
  tcs-kb-public README, docs, CI

Create or update only:
  docs/V021_COMPATIBILITY_AUDIT.md
  context/CURRENT_MILESTONE.md if needed

Audit must answer:
  1. Does workspace-template pin a compatible framework version?
  2. Can MCP server run from workspace?
  3. Can fake provider demo run from workspace?
  4. Is public KB still readonly?
  5. Are accepted artifacts untouched?
  6. Are CI commands documented?
  7. Are all known limitations clear?

Rules:
  1. Audit only.
  2. No runtime behavior changes.
```

Acceptance criteria:

```text
1. Compatibility report exists.
2. No accepted KB changes.
3. Any cross-repo gaps are listed as follow-ups.
```

---

## Task V.2: v0.2.1 release candidate

```text
Repository:
  tcs-cosheaf

Branch:
  release-v021-agent-access-rc

Goal:
  Prepare v0.2.1 as the Agent Access + Hosted API Provider release candidate.

Allowed changes:
  pyproject.toml
  cosheaf/__init__.py if version lives there
  docs/releases/v0.2.1.md
  README.md
  RELEASE_CHECKLIST.md
  context/CURRENT_MILESTONE.md

Release must claim:
  1. MCP read-only + controlled-write agent interface.
  2. Skill/operator package.
  3. Hosted provider gateway with fake + OpenAI-compatible transport.
  4. Internal orchestrator can dispatch hosted API workers when explicitly configured.
  5. External agents can use Cosheaf through MCP.
  6. No automatic accepted promotion.
  7. Not production multi-user platform.

Before finishing:
  make lint
  make typecheck
  make test
  make validate
  make gate
```

Acceptance criteria:

```text
1. Release notes are conservative and accurate.
2. No secret/API key required.
3. Workspace-template and public KB compatibility checked.
4. Current milestone points to post-v0.2.1 work or release completion.
```

---

# 9. Model / Provider policy details

## 9.1 Provider-neutral config

```yaml
provider: fake | openai_compatible | anthropic | google | local | custom
model: string
temperature: number | null
top_p: number | null
reasoning_effort: low | medium | high | null
max_output_tokens: integer
tool_policy: none | read_only | local_tools | verifier_tools
network_policy: disabled | explicit_allow
policy_mode: public_only | private_research
allowed_kb_roots: list[string]
confirm_send: boolean
```

要求：

```text
1. 默认 provider 必须是 fake 或 disabled。
2. 测试只能使用 fake/mocked provider。
3. hosted provider 必须显式启用。
4. 参数不被 provider 支持时，不得崩溃；必须记录 capability negotiation。
5. 系统可靠性不得依赖 temperature。
6. 每次真实 provider 调用必须留下 ProviderRunRecord。
7. private context 发送必须经过 policy filter + preview + consent。
```

## 9.2 默认角色策略

```text
orchestrator:
  randomness: low
  reasoning_effort: medium
  goal: planning, routing, summarizing
  may call hosted workers only when configured

librarian:
  randomness: lowest
  reasoning_effort: low
  goal: retrieval, ranking, audit
  cannot create new claims

verifier:
  randomness: lowest
  reasoning_effort: medium
  goal: adversarial checking
  cannot mark accepted/human_reviewed

reasoner:
  randomness: medium only when exploring alternatives
  reasoning_effort: medium/high
  goal: candidate generation
  must mark assumptions and uncertainty

explorer/counterexampleer:
  randomness: low-to-medium
  use parallel attempts rather than one high-temperature attempt
  must preserve failed paths

formalizer:
  randomness: low
  reasoning_effort: medium/high
  goal: precise mapping and convention analysis
  cannot claim semantic alignment without human review
```

禁止：

```text
1. 全局高 temperature。
2. 单次高温输出直接进入 artifact。
3. 把 model parameter 写死在业务逻辑里。
4. 测试依赖随机输出。
5. Hosted verifier 用自然语言判断替代 deterministic verifier result。
```

---

# 10. WorkerBundle discipline

WorkerBundle 必须表达失败、不确定性和风险。

```text
Required fields:
  bundle_id
  task_id
  worker_role
  provider
  model
  created_at
  summary
  used_artifacts
  used_sources
  claims
  proposed_artifacts
  verification_requests
  failures_or_counterexamples
  risk_flags
  confidence
  next_steps
  output_paths
```

规则：

```text
1. Any worker output path must be repo-local.
2. Output path must not be kb/accepted/.
3. Proposed artifacts default to draft/proposal.
4. Claims must distinguish known facts, assumptions, conjectures, and unchecked steps.
5. Bundle validation failure blocks reducer.
6. Reducer must preserve failure/risk/uncertainty.
7. Hosted API output must pass same bundle validation as local worker output.
```

---

# 11. 每个 PR 的 Definition of Done

Codex 完成任一 Task 前必须检查：

```text
1. Scope 没有扩大。
2. 没有直接写 kb/accepted/，除非 Task 明确要求且 promotion/review 条件满足。
3. 没有 public/private 依赖方向错误。
4. 没有把 skipped verifier 当 pass。
5. 没有把 AI output 标成人工 review。
6. 没有真实 hosted API 默认启用。
7. 没有真实 API/network 测试。
8. 新 public interface 更新了 INTERFACE_REGISTRY。
9. 新架构选择写了 ADR。
10. 新行为有测试。
11. CLI 有 smoke test。
12. MCP tool 有 allow/deny 测试。
13. Provider gateway 有 fake/mocked 测试。
14. Gate 有 pass/fail test。
15. docs 与 PROJECT_STATE/CURRENT_MILESTONE 已更新。
16. 已运行所有可用 make 命令。
17. 无法运行的命令已如实报告。
```

PR summary 模板：

```text
Goal:
Scope:
Files changed:
Tests run:
Commands unavailable:
Invariants checked:
Security/privacy impact:
Known limitations:
Follow-up tasks:
```

---

# 12. Stop rules

遇到以下情况必须停止并请求 maintainer 决策：

```text
1. 需要新增第四个核心仓库。
2. 需要改变 public/private dependency policy。
3. 需要允许 agent/MCP/provider 写 accepted artifact。
4. 需要把 AI review 当 human review。
5. 需要真实 API key 或真实网络测试。
6. 需要把真实 provider 设为默认 CI 路径。
7. 需要改变 license。
8. 需要大规模重构现有模块。
9. 需要 mass import public KB artifacts。
10. 需要声称 Lean/mathlib/CSLib semantic alignment 已自动完成。
11. 需要删除现有 gate/review/promotion 约束。
12. 需要把 sidecar index 当作 source of truth。
13. 需要 MCP 暴露 arbitrary shell。
14. 需要 MCP 暴露 promote/write accepted。
15. 需要默认发送 private KB 给 hosted provider。
16. 需要提交 API key、private logs、provider raw prompts 到 Git。
```

---

# 13. 回滚规则

```text
1. MCP 一旦暴露 arbitrary shell，回滚。
2. MCP 一旦能写 kb/accepted/，回滚。
3. MCP controlled-write 一旦不需要 allow-write，回滚。
4. Provider gateway 一旦真实联网进入 CI，回滚。
5. Provider gateway 一旦记录 API key，回滚。
6. Provider gateway 一旦默认发送 private KB，回滚。
7. Hosted worker 一旦能直接 accepted promotion，回滚。
8. Skill 一旦包含 private KB 或声称可绕过 gate，回滚。
9. Service layer 一旦改变 CLI 既有语义且无迁移说明，回滚。
10. Any new tool missing optional dependency causing validate/gate/test failure，回滚。
```

---

# 14. 最小下一步

如果用户没有指定具体任务，Codex 只能执行：

```text
Phase R / Task R.1: v0.2.0 基线审计与定向回退报告
```

完成后停止。

不得直接开始实现 service layer、MCP、Skill、provider gateway、hosted workers 或 release。第一步必须先确认 current main 相对 v0.2.0 的实际差异。
