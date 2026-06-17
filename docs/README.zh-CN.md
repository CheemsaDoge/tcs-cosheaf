# TCS-Cosheaf 中文文档导航

本页为中文读者提供 TCS-Cosheaf 文档入口和阅读顺序。英文文档仍是项目接口、架构、流程和 release 状态的权威来源；中文页面用于降低上手成本，并帮助读者快速定位相关英文文档。

## 推荐阅读顺序

1. [项目中文简介](../README.zh-CN.md)：了解项目目标、当前状态、快速开始和常用命令。
2. [Product spec](PRODUCT_SPEC.md)：理解产品边界、用户场景和当前能力。
3. [Architecture](ARCHITECTURE.md)：理解仓库即项目记忆、artifact、验证、gatekeeper、索引和智能体 harness 的整体结构。
4. [Workspace quickstart](WORKSPACE_QUICKSTART.md)：学习如何使用 `cosheaf.toml` 组合框架、只读公共 KB 和可写私有 KB。
5. [Public/private KB policy](PUBLIC_PRIVATE_KB.md)：理解公开知识库和私有研究覆盖层的隔离规则。
6. [Gates](GATES.md)：理解验证和门禁语义，尤其是 `skipped` 不是 `pass`。
7. [Artifact lifecycle](ARTIFACT_LIFECYCLE.md)：理解 draft、locally tested、reviewed、accepted、refuted、obsolete 等生命周期状态。
8. [Codex workflow](CODEX_WORKFLOW.md)：理解 issue 驱动开发、上下文包、分支、PR 和检查命令。
9. [Agent access](AGENT_ACCESS.md)、[Codex operator runbook](CODEX_OPERATOR_RUNBOOK.md)、[Research loops](RESEARCH_LOOPS.md) 与 [Reviewable workflows](WORKFLOWS.md)：理解 CLI-first 智能体接口、受限 operator 流程、bounded research-loop 和 v0.9.0 workflow 边界。
10. [Agent providers](AGENT_PROVIDERS.md)：理解提供商边界、真实网络调用保护和日志策略。
11. [Current milestone](../context/CURRENT_MILESTONE.md) 与 [Project state](../context/PROJECT_STATE.md)：查看当前里程碑和持久化项目状态。

## 核心概念速查

- **Artifact**：定义、命题、证明、构造、算法、归约、反例、实验、评审、验证器或 issue 等带类型研究记录。
- **Accepted knowledge**：位于 `kb/accepted/` 的已接受知识。accepted artifact 不能依赖 draft 或未接受 artifact。
- **Draft knowledge**：位于 `kb/draft/` 的草稿或提升前知识。
- **Workspace**：由 `cosheaf.toml` 描述的多 KB 根配置，通常包含只读公共 KB 和可写私有 KB。
- **Gatekeeper**：把 schema、依赖、证据、验证器和评审不变量转化为可读/机器可读报告的检查层。
- **Context pack**：面向某个 issue 的确定性、排序后、大小受控上下文包，用于 Codex 或其他智能体任务。
- **Verifier adapter**：把外部检查器结果规范化为 `pass`、`fail`、`error` 或 `skipped` 的接口。

## 工作流要点

- 非平凡工作应由 issue 驱动：一个 issue、一个聚焦分支、一个 PR、一个可审查增量。
- 仓库文件是项目记忆；重要决策、接口、状态、限制和评审证据应写回仓库。
- 公开行为变化需要测试；公共接口变化需要更新 `context/INTERFACE_REGISTRY.md`。
- 架构变化需要在 `docs/ADR/` 下记录 ADR。
- 缺失可选外部工具应产生 `skipped` 或 unavailable 结果，而不是核心系统崩溃。
- `skipped` 不是 `pass`，不得用跳过结果声称验证成功。
- accepted knowledge 必须通过 `cosheaf artifact promote <artifact-id>` 进入生命周期 KB 根，不能手动移动 YAML 文件。

## 常用命令

```bash
make lint
make typecheck
make test
make validate
make gate
```

```bash
cosheaf validate
cosheaf gate
cosheaf workspace info
cosheaf context build <issue-id>
cosheaf index rebuild
cosheaf graph show
```

## 文档地图

### 使用与工作区

- [README](../README.md)：英文项目首页。
- [中文 README](../README.zh-CN.md)：中文项目首页。
- [Workspace quickstart](WORKSPACE_QUICKSTART.md)：工作区快速开始。
- [Workspace model](WORKSPACE.md)：工作区配置和 KB layering 规则。
- [Public/private KB policy](PUBLIC_PRIVATE_KB.md)：公共/私有知识库策略。

### Artifact、验证与门禁

- [Artifact schema](ARTIFACT_SCHEMA.md)：artifact 字段和 schema 说明。
- [Artifact lifecycle](ARTIFACT_LIFECYCLE.md)：artifact 生命周期和提升协议。
- [Gates](GATES.md)：gatekeeper 和验证门禁。
- [Review policy](REVIEW_POLICY.md)：人工评审和机器证据边界。
- [Formalization links](FORMALIZATION_LINKS.md)：Formal Link Layer 和 Lean 引用语义。

### 智能体与提供商

- [Codex workflow](CODEX_WORKFLOW.md)：Codex 开发流程。
- [Agent access](AGENT_ACCESS.md)：CLI-first 智能体访问接口。
- [Codex operator runbook](CODEX_OPERATOR_RUNBOOK.md)：operator 命令入口和安全边界。
- [Research loops](RESEARCH_LOOPS.md)：bounded multi-attempt research-loop 运行时、attempt memory 和 scanner。
- [Reviewable workflows](WORKFLOWS.md)：v0.9.0 初始 workflow CLI、未实现项和 review-context 边界。
- [Agent providers](AGENT_PROVIDERS.md)：提供商配置、fake provider 和真实网络边界。
- [Agent roles](AGENT_ROLES.md)：智能体角色合同。
- [MCP server](MCP_SERVER.md)：MCP 接口。

### 项目状态、路线图与发布

- [Roadmap](ROADMAP.md)：路线图。
- [Current milestone](../context/CURRENT_MILESTONE.md)：当前里程碑。
- [Project state](../context/PROJECT_STATE.md)：持久化项目状态。
- [Interface registry](../context/INTERFACE_REGISTRY.md)：公共接口登记表。
- [Release checklist](../RELEASE_CHECKLIST.md)：发布检查清单。
- [Release notes](releases/)：版本发布记录。

## 维护说明

中文文档应保持与英文权威文档一致。当英文文档中的公共接口、工作流、架构或 gate 语义变化时，应同步更新本导航或中文简介，避免中文读者使用过期流程。
