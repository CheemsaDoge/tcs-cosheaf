# TCS-Cosheaf 中文简介

TCS-Cosheaf 是一个以 Git 为持久记忆层的、带类型约束的理论计算机科学研究知识库与智能体协作框架。它把定义、命题、证明、构造、算法、归约、反例、实验、评审、议题和验证器证据保存为可审查的仓库文件，而不是只保存在聊天记录中。

> 当前状态：**v0.6.0 Operator Session + Review Handoff release**。
> 包版本记录为 `0.6.0`；公开 `v0.6.0` tag 和 GitHub release 已发布；
> 从 `@v0.6.0` 的 post-tag release smoke 已通过；workspace-template 与
> public KB downstream pin 已更新到 `@v0.6.0`。本版本加入 operator session、
> 可选 MCP session recording、leak scanning、handoff bundle、
> review-context handoff export、下游 demo/policy smoke 和 ecosystem matrix
> 覆盖。当前未发布主线正在推进 `v0.7.0` Bounded Research Loop + Attempt Memory：
> Phase B 已加入 `.cosheaf/research-loops/` 运行时记录，C.1 已加入
> `next/step/run --dry-run/export-task/import-result` 的受限 CLI surface，
> D.1 已加入运行时 attempt memory、重复失败规避、`retry_justification`
> 检查和 loop scanner。Phase E 已开始加入确定性的 research-loop eval 与
> framework ecosystem smoke rows；workspace-template demo 与 public-KB policy
> alignment 仍是后续单独 PR。
> 这些内容尚未发布，也不授予 accepted 写入、人类评审、验证器通过、
> gate 通过或 promotion 权限。它仍不是生产就绪软件，也不提供 Web UI、
> 默认真实托管提供商路径、自动定理证明、完整 Lean 自动形式化、自动 accepted
> 提升或多用户权限系统。

## 为什么需要它

理论计算机科学研究经常在论文、聊天、脚本和本地文件之间分散保存命题、证明尝试、构造、反例、实验和评审记录。随着项目增长，团队很难回答：

- 哪些命题已经 accepted、仍是 draft、已 refuted，或已 obsolete？
- 一个研究 artifact 依赖哪些假设和前置结果？
- 哪些证据由什么命令、在什么仓库状态下检查过？
- 人类或智能体处理某个 issue 前应该读取哪些上下文？

TCS-Cosheaf 的核心做法是把仓库视为项目记忆，使研究状态可以被 Git 审查、验证、索引，并以有限上下文交给 Codex 或其他智能体。

## 核心思路

- 以 YAML 文件保存带类型的研究 artifact。
- 校验 schema、ID、状态/路径不变量、依赖关系和本地证据路径。
- 构建确定性的依赖图和 SQLite/manifest 索引。
- 在接受行为或知识变更前运行 gatekeeper 检查。
- 通过可选适配器规范化验证器输出。
- 为 issue 生成排序后的、大小受控的上下文包。
- 以显式本地 worker 命令运行任务，并验证结构化输出 bundle；不会自动合并 accepted knowledge。
- 通过 Formal Link Layer 记录外部形式化声明的元数据引用，而不是复制 Lean 证明。

可选形式化工具保持可选。缺失 SAT、SMT、Lean 或类似工具时，应产生 `skipped` 验证结果，而不是让核心系统崩溃；`skipped` 也不能被当作 `pass`。

## 快速开始

本仓库是框架包。面向用户的研究工作区建议从 `tcs-cosheaf-workspace-template` 开始，而不是手动合并框架仓库和知识库仓库。预期模型是：

- `tcs-cosheaf`：框架、CLI、schema、gates 和智能体 harness。
- `tcs-kb-public`：可复用的公开 TCS 知识库，通常以只读方式挂载。
- `tcs-cosheaf-workspace-template`：用户入口，组合只读公共 KB 与可写 `kb/private` 覆盖层。

安装开发环境：

```bash
git clone https://github.com/CheemsaDoge/tcs-cosheaf.git
cd tcs-cosheaf
python -m pip install -e ".[dev]"
```

查看 CLI：

```bash
cosheaf --help
cosheaf version
cosheaf workspace info
```

运行验证和门禁：

```bash
cosheaf validate
cosheaf gate
```

创建并移动草稿生命周期 artifact：

```bash
cosheaf artifact create --id claim.example.new --type claim --title "New claim" --domain graph-theory --status draft --statement "Statement under review."
cosheaf artifact move-status claim.example.new locally_tested
```

提升符合条件且经过评审的 artifact：

```bash
cosheaf artifact promote claim.example.new
```

直接创建 accepted artifact、或直接执行 `move-status ... accepted` 都会被拒绝。提升流程需要通过仓库验证、gatekeeper、目标验证器、依赖和评审检查。

## 常用开发命令

```bash
make lint
make typecheck
make test
make validate
make gate
```

`make validate` 运行当前仓库验证 CLI。`make gate` 运行 gatekeeper 并把报告写入 `.cosheaf/reports/`。未提供 PR checklist 源时 G8 为 `skipped`；可使用 `cosheaf gate run --pr-checklist <path>` 检查本地 PR 正文 Markdown。

## 重要文档

中文入口：

- [中文文档导航](docs/README.zh-CN.md)

英文权威文档：

- [Project rules](AGENTS.md)
- [Product spec](docs/PRODUCT_SPEC.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Workspace quickstart](docs/WORKSPACE_QUICKSTART.md)
- [Workspace model](docs/WORKSPACE.md)
- [Public/private KB policy](docs/PUBLIC_PRIVATE_KB.md)
- [Gatekeeper and validation gates](docs/GATES.md)
- [Agent access](docs/AGENT_ACCESS.md)
- [Codex operator runbook](docs/CODEX_OPERATOR_RUNBOOK.md)
- [Research loops](docs/RESEARCH_LOOPS.md)
- [Agent providers](docs/AGENT_PROVIDERS.md)
- [Evaluation](docs/EVALUATION.md)
- [Artifact lifecycle](docs/ARTIFACT_LIFECYCLE.md)
- [Artifact schema](docs/ARTIFACT_SCHEMA.md)
- [Codex workflow](docs/CODEX_WORKFLOW.md)
- [Review policy](docs/REVIEW_POLICY.md)
- [Release checklist](RELEASE_CHECKLIST.md)
- [Current milestone](context/CURRENT_MILESTONE.md)
- [Project state](context/PROJECT_STATE.md)
- [Public interface registry](context/INTERFACE_REGISTRY.md)

## 非目标

MVP 不追求以下能力：

- Web UI。
- 模型训练。
- 自动定理证明智能体。
- 完整 Lean 自动形式化。
- 多用户权限系统。
- 替代同行评审、形式化证明助手或领域专家判断。
- 替代 CSLib、mathlib、Lean 或人工语义对齐评审。

## 许可证

本项目使用 [Apache License 2.0](LICENSE)。
