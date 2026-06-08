[中文版](CODEX_WORKFLOW.zh-CN.md) | [English](CODEX_WORKFLOW.md)

# Codex 工作流 (Codex Workflow)

## 仓库记忆 (Repository Memory)

Codex 的对话不是项目记忆。代码仓库才是项目记忆。

持久的项目决策、当前状态、公共接口、里程碑和工作流规则必须记录在仓库文件中。未来的任务不应该依赖仅保存在聊天记录中的假设。

## 操作范围 (Operating Scope)

TCS-Cosheaf 正在向三仓库架构演进：

- `tcs-cosheaf` 是框架仓库，包含 CLI、Schema、工件模型、验证、网关检查器（gatekeeper）、验证器适配器（verifier adapters）、上下文包机制、工作区配置支持和工作流规则。
- `tcs-kb-public` 是公共的可复用 TCS 知识库，包含公开的、可引用的定义、已知定理、构造、归约、反例以及来源元数据。
- `tcs-cosheaf-workspace-template` 是面向用户的工作区模板，结合了框架包、只读的公共 KB（知识库）和可写的私有 KB 覆盖层。

用户不应该手动合并框架和 KB 仓库。工作区应当使用 `cosheaf.toml`，使框架包、只读公共 KB 和可写私有 KB 覆盖层感觉像是一个可用的环境。私有工件可以依赖公共工件；公共工件不能依赖私有工件。已接受（Accepted）的工件不能依赖草稿（draft）工件，即使跨越了不同的 KB 根目录也是如此。

## 必读内容 (Required Reading)

每项任务必须阅读：

- `AGENTS.md`。
- `docs/` 目录下的相关文件。
- `context/` 目录下的相关文件。

改变架构的任务必须阅读现有的 ADR（架构决策记录）。改变公共接口的任务必须阅读 `context/INTERFACE_REGISTRY.md`。

## 任务形态 (Task Shape)

一个任务 = 一个分支 = 一个 PR。任务应该足够小，以便进行审查、验证和精确描述。

不要运行过于庞大的任务。将广泛的工作拆分为有序的分支，并提供清晰的交接说明和后续任务。

## GitHub 工作流 (GitHub Workflow)

拉取请求（Pull requests）是 Codex 任务的审查单元。每个 PR 应使用仓库的拉取请求模板，并明确记录摘要、更改的文件、运行的测试、风险、接口更改、文档更改、工件/Schema 更改以及网关检查器（gatekeeper）的结果。

在进行非平凡的新工作之前，请检查现有的 issue。如果没有相关的 issue，并且可以创建 GitHub issue，请为该工作创建一个聚焦的 issue。如果由于缺少 `gh`、未认证或未授权而无法创建 GitHub issue，请在 `issues/open/` 下创建一个本地 Markdown 格式的 issue 草稿，明确报告跳过了远程 issue 的创建，不要假装已经创建了 GitHub issue。

分支默认应命名为 `codex/<任务ID或简短名称>`。如果 issue、维护者或发布工作流指定了不同的人类可读分支名称，请保留该确切的分支名称。不要直接推送到 `main` 分支。保持每个 PR 规模小且易于审查，不要将不相关的路线图项目合并到一个 PR 中。

分支保护和审查要求记录在 [`docs/REVIEW_POLICY.md`](REVIEW_POLICY.md) 中。不允许直接推送到 `main`。所有更改应遵循 issue -> 分支 -> PR -> CI/网关检查 -> 审查 -> 合并 的工作流。

我们提供了用于特性任务、错误任务和研究 issue 的 GitHub issue 表单。特性任务 issue 应通过目标、允许修改的文件、验收标准、所需运行的命令和上下文包路径来约束 Codex 的工作。研究 issue 应记录问题陈述、领域、已知基线、相关工件、预期证据和所需的网关检查。错误任务 issue 应记录观察到的行为、预期行为、重现步骤、日志以及怀疑的模块。

GitHub Actions CI 在拉取请求和推送到 `main` 分支时运行，使用 Python 3.11。CI 会安装该包及其开发依赖，然后运行：

- `make lint`
- `make typecheck`
- `make test`
- `make validate`
- `make gate`

CI 不得要求提供可选的外部形式化工具（如 Lean、Sage、Z3、cvc5 或 SAT 求解器）。测试不得进行网络调用。

## 接口和架构更改 (Interface and Architecture Changes)

公共接口的更改需要更新 `context/INTERFACE_REGISTRY.md` 中的 INTERFACE_REGISTRY。

架构更改需要 ADR。

## 工作区配置 (Workspace Configuration)

在假设仅有单一 KB 树之前，请使用 `cosheaf workspace info` 检查活动的工作区。如果没有 `cosheaf.toml`，仓库将在遗留模式下运行，并在 `kb/` 处拥有一个可写的 KB 根目录。

当存在 `cosheaf.toml` 时，`[workspace]` 表会命名工作区，每个 `[[kb]]` 表声明一个 KB 根目录，包含 `name`、相对于仓库的 `path`、`readonly` 和 `priority` 字段。存储发现机制会读取配置的 KB 根目录，加上仓库本地的 `issues/` 和 `examples/`。

私有工件可以依赖公共工件。公共工件不得依赖私有工件。已接受的工件不得依赖草稿或预先接受（pre-accepted）的工件，即使跨 KB 根目录。不要手动合并框架和 KB 仓库。

生命周期写入命令尊重只读根目录。默认情况下，配置工作区中的 `cosheaf artifact create` 会写入可写的私有根目录，而 `cosheaf artifact move-status` 会拒绝从只读根目录加载的记录。

## 验证 (Verification)

不要隐藏验证失败。如果预期的命令尚不存在，任务必须实现它，或者明确说明为何尚未提供该命令。

跳过（Skipped）不等于通过（pass）。可选外部工具缺失应产生一个已跳过的验证器结果，而不是导致核心工作流崩溃。预期的验证失败应该被清晰地报告；不应该吞没意外错误。不要为了让测试通过而削弱测试，不要将占位符行为标记为完成。

## 仓库创建 (Repository Creation)

当任务要求 Codex 创建仓库时，首先运行 `gh --version` 和 `gh auth status`。仅当 GitHub CLI 存在、已认证且已授权时才创建仓库。在创建后验证远程仓库是否存在，并尽可能开启一个 PR。

永远不要伪造仓库创建、分支创建、issue 创建、PR 创建、远程推送或通过的检查。如果任何 GitHub 步骤失败，请报告确切的阻塞原因及最诚实的下一步。

## 工件生命周期命令 (Artifact Lifecycle Commands)

当工件要进入生命周期树时，请使用 `cosheaf artifact create` 创建新的工件记录，而不是手动编写 YAML。该命令会根据工件类型、状态和 ID 派生出仓库路径，拒绝重复的 ID，并在报告成功前验证新文件。

使用 `cosheaf artifact move-status <artifact-id> <new-status>` 进行生命周期状态移动，而不是手动移动文件。该命令会检查当前的工件路径是否已符合其当前状态，在移动前验证仓库，写入确定性的 YAML，并拒绝直接移动为 `accepted`。

使用 `cosheaf artifact promote <artifact-id>` 将符合条件的工件提升为已接受的知识。晋升操作会验证仓库，运行网关检查器，拒绝阻塞性的网关问题，拒绝目标验证器的 `fail` 或 `error` 结果，要求 `review.state` 为 `human_reviewed` 或 `accepted`，要求依赖项是已接受的本地工件或显式的外部引用，并将确定性的 YAML 写入 `kb/accepted/<type-dir>/<artifact-id>.yaml`。

不要手动将工件移动到 `kb/accepted/` 中。直接创建 accepted 状态的工件或使用 `cosheaf artifact move-status <artifact-id> accepted` 依然会被拒绝。Issue、任务和审查记录不是生命周期工件，绝不能使用 `artifact promote` 进行提升。

## 本地任务运行器 (Local Task Runner)

仅在针对现有任务记录执行显式本地命令时，使用 `cosheaf task run <task-id> -- <command> [args...]`。本地运行器不是 LLM 运行时，不会调用托管的模型提供商，也不会添加网络服务调用。它使用 `shell=False` 执行 argv 列表，强制执行超时机制，默认在仓库根目录下运行，仅允许传递仓库本地的 `--cwd` 值，并在执行命令前拒绝仓库外部的 bundle 路径。它会将 stdout、stderr、返回码、命令元数据以及可选的 bundle 验证状态记录在 `.cosheaf/tasks/<task-id>/runs/<run-id>/` 下。

在命令成功执行后，使用 `--bundle <path>` 来验证 worker 输出包（bundle）而不完成任务。仅当命令成功且应当通过现有的编排器存根完成任务时，才使用 `--complete-with-bundle <path>`。包（bundle）路径必须是仓库本地的 YAML 清单或包含 `bundle.yaml` 的仓库本地目录。这两种模式都不会将输出合并到已接受的知识中或提升工件。已接受的知识仍然仅通过审查、网关和 `cosheaf artifact promote` 进入。

## 上下文包 (Context Packs)

使用 `cosheaf context build <issue-id>` 在 `context/TASKS/<issue-id>/` 下生成有边界的任务上下文包。

每个上下文包包含：

- `CONTEXT.md`
- `ACCEPTANCE.md`
- `RELEVANT_ARTIFACTS.md`
- `KNOWN_FAILURES.md`
- `COMMANDS.md`

上下文包是确定性的、具有 issue 作用域的，并且有意设计得简短。它们默认不会包含所有的仓库工件。相关工件通过可解释的本地原因进行排名：

- 来自 issue 的直接引用；
- 直接引用的工件的一跳依赖邻居；
- 工件所属领域与 issue 的标题、描述或标签匹配；
- 工件标签与 issue 标签匹配。

在同一个相关性类别中，已接受的工件优先于草稿工件。草稿工件会显式标记为 `[DRAFT]`。被反驳、废弃和被取代的工件仅在与 issue 匹配且带有最终状态标记时显示，不会被作为当前事实呈现。

使用 `cosheaf context show <issue-id>` 构建包并打印主要上下文文档，以便快速交接到新的 Codex 对话中。

## 交接 (Handoff)

用户交接消息应使用中文编写。面向项目的文档应保持英文，除非任务明确要求使用其他语言。