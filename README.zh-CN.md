# TCS-Cosheaf

[中文版](README.zh-CN.md) | [English](README.md)

TCS-Cosheaf 是一个基于 Git 的类型化研究知识库及智能体演练框架（agent harness），旨在辅助理论计算机科学（theoretical computer science, TCS）的 AI 研究。它将定义、断言、证明、构造、算法、归约、反例、实验、评审、问题（issues）和验证器证据（verifier evidence）等保存在可供审查的代码库文件中。

当前状态：**v0.1.1 形式化链接层（Formal Link Layer）支持发布 / 最小可行性产品前（pre-MVP）脚手架**。该代码库已具备可用的 Python 脚手架、类型化构件（artifact）模型、文件系统加载、验证（validation）、依赖图索引、支持工作区的知识库（KB）根加载、构件生命周期 CLI 命令、包含 G10 形式化链接门控（Formal Link Gate）的网关检查器（gatekeeper）报告、具有紧凑形式化链接显示的排序上下文包（context-pack）生成、本地任务演练存根（local task harness stubs）、验证器适配器（包含一个 Python 检查器、一个最小可选的 SAT DIMACS 路径、一个最小可选的 SMT-LIB 路径）、GitHub Actions CI，以及协作模板。Python 包元数据被设置为 `0.1.1`，以支持形式化链接层支持版本的发布。它目前不是生产级软件，尚未提供 Web 用户界面、自动定理证明、完整的 Lean 自动化形式化（autoformalization），或多用户权限功能。

## 面临的问题 (Problem)

在理论计算机科学的研究项目中，断言、证明尝试、构造、反例、实验和评审记录等通常分散在论文、聊天记录、脚本和本地文件中。这导致我们很难回答以下基本问题：

- 哪些断言是被接受的、草稿状态、被反驳的或是已废弃的？
- 哪些构件依赖于哪些假设？
- 哪些证据经过了检查，使用了什么命令，以及基于代码库的哪个状态？
- 人类或智能体（agent）在处理某个问题之前应该阅读什么上下文？

TCS-Cosheaf 将代码库视为持久的项目记忆（project memory），因此可以在不依赖于对话历史的情况下对研究状态进行审查、验证、索引并移交给智能体。

## 解决途径 (Approach)

- 将类型化的研究构件存储为基于 Git 的 YAML 文件。
- 验证构件的形态（shape）、ID、状态/路径不变量（invariants）、依赖关系，以及本地证据路径。
- 构建确定性的依赖图和代码库索引。
- 在接受行为或构件变更之前，运行网关检查器（gatekeeper）进行拦截验证。
- 通过可选的适配器规范验证器（verifier）输出。
- 为基于问题范围（issue-scoped）的 Codex 或智能体任务，生成排序后的有界上下文包。
- 针对问题范围的任务，运行显式的本地工作节点（worker）命令，并验证结构化输出包，而不会自动合并已被接受的知识。
- 通过形式化链接层（Formal Link Layer），记录仅含元数据的对外部形式化声明的引用，而无需复制 Lean 证明。

可选的形式化工具保持可选状态。如果缺失 SAT、SMT、Lean 或类似工具，系统必须产生跳过（skipped）验证的结果，而不是使核心系统崩溃。
Cosheaf 不会取代 CSLib、mathlib 或 Lean：形式化链接仅代表元数据加上网关、上下文包、索引及查询接口。未来工作将继续支持针对 CSLib/mathlib 引用的外部 Lean `#check` 支持。

## 当前状态 (Current Status)

已实现 (Implemented):

- 带有 Typer CLI 的 Python 3.11+ 包脚手架。
- Pydantic v2 构件模型及状态辅助工具。
- 初始 JSON Schema 及示例 YAML 记录。
- 基于文件系统的构件/问题/评审加载，及确定性的 YAML 写入。
- 可选的 `cosheaf.toml` 工作区配置，支持多个知识库根（KB roots）、只读根、公共/私有依赖策略，及向后兼容的回退方案。
- `cosheaf validate`, `cosheaf artifact validate <path>`, `cosheaf artifact create`, `cosheaf artifact move-status`, `cosheaf artifact promote` 和 `cosheaf workspace info` 命令。
- 依赖图审查机制，及确定性的 SQLite/清单索引（manifest index）重建。
- 通过 `ArtifactIndexQuery` 提供的针对重建索引输出的只读 SQLite 查询 API，包括构件、状态、类型、领域、依赖、反向依赖、形式化及形式化策略查询。
- `cosheaf gate` 和 `cosheaf gate run` 报告生成。
- 通过 `cosheaf context build <issue-id>` 生成排序后的问题范围（issue-scoped）上下文包。
- 形式化链接层构件元数据字段：`formalizations`、`alignment` 及 `verification_policy`。
- G10 形式化链接门控（Formal Link Gate）的静态元数据一致性检查。
- SQLite `formalizations` 和 `artifact_formal_policy` 索引表，以及紧凑的清单元数据。
- 上下文包中显示形式化链接元数据，不对 Lean 验证或非形式化/形式化对齐进行断言。
- 本地任务演练存根，包含 `cosheaf task create`, `cosheaf task list` 和 `cosheaf task complete`。
- 验证器适配器协议、Python 检查器适配器、最小可选的 SAT DIMACS 适配器、最小可选的 SMT-LIB 适配器以及最小可选的 Lean 纯文件适配器。
- 可执行证据验证结果的复现性元数据门控。
- 通过 `cosheaf gate run --pr-checklist <path>` 提供本地 PR 检查清单门控支持。
- 首个图论（graph-theory）试点工作流，包括草稿构件证据和本地 Python 检查器。
- 第二个 SAT/CNF 试点工作流，包括可选的 SAT 证据、已知满足分配以及作为后备方案的 Python 检查器。
- GitHub Actions CI，包含独立运行的 `lint`、`typecheck`、`test`、`validate` 和 `gate` 检查。

规划中或未完成 (Planned or incomplete):

- 在最小可选 DIMACS 调用路径之上的完整 SAT 后端覆盖。
- 在最小可选 SMT-LIB 调用路径之上的完整 SMT 后端覆盖。
- 在最小可选纯文件调用路径之上的完整 Lean 证明助手（proof-assistant）集成。
- 除了显式的本地 Markdown 文件之外的托管 PR 检查清单源发现功能。
- 托管 LLM/模型提供商（model-provider）工作节点执行。
- 除了本地工作区根之外的外部公共知识库代码库集成。
- 针对 CSLib/mathlib 声明的外部 Lean 库引用检查。
- 自动化的非形式化/形式化语义对齐检查。

## 工作节点与编排器边界 (Worker And Orchestrator Boundary)

TCS-Cosheaf 包含一个轻量级的本地任务执行层。任务是问题范围的记录，上下文包提供了受限的代码库上下文，且本地工作节点运行会执行显式命令的 argv 列表，并包含代码库本地的工作目录、超时元数据，以及 stdout、stderr 和返回码（return-code）记录。工作节点可以返回结构化输出包，现有的契约将对其进行审查验证。

当前的编排器（orchestrator）是一个本地文件系统存根（stub）。它不调用托管的 LLMs 或模型提供商，不运行网络服务，不合并工作节点的输出，也不会晋升（promote）已接受的知识。已接受知识的引入依然需要经过评审、门控和 `cosheaf artifact promote`。

## 核心概念 (Core Concepts)

- **构件 (Artifact)**：一种类型化的研究记录，如定义、断言、证明、构造、算法、归约、反例、实验、评审、验证器或问题。
- **状态格 (Status lattice)**：构件状态值描述生命周期状态，如 `draft`（草稿）、`accepted`（已接受）、`refuted`（已反驳）、`obsolete`（已废弃）和 `superseded`（已取代）。
- **已接受知识 (Accepted knowledge)**：`kb/accepted/` 仅包含已接受的构件。已接受的构件不得依赖于草稿构件。
- **草稿知识 (Draft knowledge)**：`kb/draft/` 包含草稿或预先接受（pre-accepted）状态的构件。
- **网关检查器 (Gatekeeper)**：代码库检查机制，将模式（schema）、依赖项、证据、验证器和评审的不变量转化为机器可读及人类可读的报告。
- **工作区 (Workspace)**：一个 `cosheaf.toml` 配置，可堆叠（layer）一个或多个知识库根（KB roots），如只读的公共知识库以及可写的私有知识库覆盖层。
- **上下文包 (Context pack)**：一个确定性的针对特定问题（issue-scoped）的排序后的代码库上下文包，提供给 Codex 或其他智能体使用。
- **验证器适配器 (Verifier adapter)**：一个可插拔的检查器接口，记录规范化的 `pass`、`fail`、`error` 或 `skipped` 结果。

## 快速开始 (Quickstart)

本代码库是框架包。如需面向用户的研究工作区，请从 [`tcs-cosheaf-workspace-template`](https://github.com/CheemsaDoge/tcs-cosheaf-workspace-template) 开始，而不是手动合并框架与知识库代码库。预期的架构模型为：

- `tcs-cosheaf`：框架、CLI、模式、网关及智能体演练框架。
- [`tcs-kb-public`](https://github.com/CheemsaDoge/tcs-kb-public)：可复用的公共 TCS 知识库，在下游工作区以只读模式挂载。
- `tcs-cosheaf-workspace-template`：用户入口点，包含一个只读的公共知识库根及一个可写的 `kb/private` 覆盖层。

私有构件可以依赖于公共构件。公共构件不得依赖于私有构件。

```bash
git clone https://github.com/CheemsaDoge/tcs-cosheaf.git
cd tcs-cosheaf
python -m pip install -e ".[dev]"
```

查看 CLI:

```bash
cosheaf --help
cosheaf version
cosheaf workspace info
```

运行代码库验证与网关检查器：

```bash
cosheaf validate
cosheaf gate
```

创建及移动草稿生命周期的构件:

```bash
cosheaf artifact create --id claim.example.new --type claim --title "New claim" --domain graph-theory --status draft --statement "Statement under review."
cosheaf artifact move-status claim.example.new locally_tested
```

将符合条件的已评审构件晋升为已接受知识:

```bash
cosheaf artifact promote claim.example.new
```

系统仍拒绝直接创建接受状态的构件以及直接运行 `move-status ... accepted`。
晋升（Promotion）过程需要通过代码库验证、网关检查、目标验证器、依赖项以及评审检查。

建立索引并审查构件依赖图:

```bash
cosheaf index rebuild
cosheaf graph show
```

为特定问题生成任务上下文:

```bash
cosheaf context build <issue-id>
cosheaf context show <issue-id>
```

请参阅 [Workspace quickstart](docs/WORKSPACE_QUICKSTART.md)、[Workspace model](docs/WORKSPACE.md) 以及 [Public/private KB policy](docs/PUBLIC_PRIVATE_KB.md) 以了解层叠式的知识库根（layered KB roots）。下游代码库应在使用构件 YAML 中的形式化（formalization）字段前，固定依赖至 `v0.1.1` 版本。

## 开发命令 (Development Commands)

```bash
make lint
make typecheck
make test
make validate
make gate
```

`make validate` 将运行当前代码库的验证 CLI 命令。`make gate` 运行网关检查器并将报告写入 `.cosheaf/reports/` 目录下。若未提供 PR 检查清单源，则会跳过 G8 检查；可以通过 `cosheaf gate run --pr-checklist <path>` 来验证本地 PR Markdown 文件正文。

## 路线图 (Roadmap)

项目路线图在 [docs/ROADMAP.md](docs/ROADMAP.md) 中进行追踪。具体的实时问题状态会在 GitHub issues 中跟踪，而非硬编码在此 README 中。

## 非目标 (Non-Goals)

针对 MVP（最小可行性产品），TCS-Cosheaf 暂不打算提供：

- Web 用户界面（Web UI）。
- 模型训练。
- 自动定理证明智能体。
- 完整的 Lean 自动化形式化。
- 多用户权限系统。
- 替代同行评审、形式化证明助手，或者领域专家判断的工具。
- 替代 CSLib、mathlib、Lean 或人类对语义对齐评审的系统。

## 核心文档 (Key Documentation)

- [项目规则](AGENTS.md)
- [产品规范](docs/PRODUCT_SPEC.md)
- [架构设计](docs/ARCHITECTURE.md)
- [工作区快速开始](docs/WORKSPACE_QUICKSTART.md)
- [工作区模型](docs/WORKSPACE.md)
- [公有/私有知识库策略](docs/PUBLIC_PRIVATE_KB.md)
- [网关检查器与验证门控](docs/GATES.md)
- [构件生命周期](docs/ARTIFACT_LIFECYCLE.md)
- [构件模式](docs/ARTIFACT_SCHEMA.md)
- [Codex 工作流](docs/CODEX_WORKFLOW.md)
- [评审策略](docs/REVIEW_POLICY.md)
- [发布检查清单](RELEASE_CHECKLIST.md)
- [当前里程碑](context/CURRENT_MILESTONE.md)
- [项目状态](context/PROJECT_STATE.md)
- [公共接口注册表](context/INTERFACE_REGISTRY.md)

## 许可证 (License)

本项目使用 [Apache License 2.0](LICENSE) 授权。