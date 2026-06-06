[中文版](ARCHITECTURE.zh-CN.md) | [English](ARCHITECTURE.md)

# 架构 (Architecture)

## 概述

TCS-Cosheaf 被组织为一个分层系统。每一层都应向上暴露狭窄的接口，并避免依赖更高层。

## 分层

### 知识层 (Knowledge Layer)

定义制品（artifact）模型、制品状态概念、制品类型词汇表、形式化链接元数据以及领域级不变量。

### 配置层 (Configuration Layer)

从 `cosheaf.toml` 加载可选的本地代码库工作区配置。当该文件不存在时，配置将回退到传统的单一根存储库行为，即在 `kb/` 下包含一个可写的知识库（KB）根目录。

工作区配置模型包含工作区名称、公开/私有策略字段，以及一个或多个 KB 根目录。每个 KB 根目录都有 `name`（名称）、相对于存储库的 `path`（路径）、`readonly`（只读）标志以及整数 `priority`（优先级）。

### 存储/索引层 (Storage/Index Layer)

从基于 Git 的路径加载制品，构建确定性的索引，并记录其他层所需的本地代码库元数据。

当存在 `cosheaf.toml` 时，存储层会在每个配置的 KB 根目录，以及本地代码库的 `issues/` 和 `examples/` 下发现 YAML 记录。加载的记录会保留它们的来源 KB 根目录名称、根路径、只读标志以及相对于 KB 根目录的路径。当 `cosheaf.toml` 不存在时，存储层将保持以前的发现根目录：`kb/`、`issues/` 和 `examples/`。

当前的索引输出为：
- `.cosheaf/index.sqlite`
- `.cosheaf/artifact_manifest.json`

索引重建会加载代码库中的 YAML 记录，规范化制品行，从头开始写入 SQLite，并输出按制品 ID 和依赖项元组排序的确定性 JSON 清单。制品行中包含来源 KB 根目录的名称。形式化链接元数据被索引到 `formalizations` 和 `artifact_formal_policy` 表中，以及紧凑的清单字段中。

SQLite 查询 API 是在 `.cosheaf/index.sqlite` 之上的一个只读便捷层。YAML 仍然是事实来源（source of truth）；调用者在 YAML 更改后查询前应重新构建索引。查询结果是确定性排序的，并公开了制品元数据、领域成员资格、依赖边缘、反向依赖边缘、形式化引用、形式策略行以及被索引的来源 KB 根目录。查询方法不会隐式地重新构建索引。

### 形式链接层 (Formal Link Layer)

记录从制品到外部形式声明的引用，目前是诸如 CSLib 或 mathlib 之类库中的 Lean 4 声明。该层在 `formalizations` 下存储库、导入路径、符号、声明种类、状态、检查模式、预期类型以及注释等元数据。

形式链接是引用，而不是复制过来的证明主体。Cosheaf 不替代 CSLib、mathlib 或其他形式化库，制品 YAML 也不应打包（vendor）Lean 证明。非形式化制品陈述与形式化声明之间的语义对齐被单独记录在 `alignment` 下；进行一次 Lean 运行并不会自动证明非形式化与形式化的对齐。

`verification_policy` 记录了一个制品是否预期进行形式链接、Lean 检查或对齐审查。G10 形式链接门禁（Formal Link Gate）会强制执行 `verification_policy`、`formalizations` 和 `alignment` 之间的静态一致性。该门禁不会执行 Lean、获取外部库、证明非形式化/形式化对齐，也不会改变“接受”（accepted）晋升的语义。形式链接的上下文包（context-pack）显示和 SQLite/查询支持都是建立在相同制品字段之上的纯元数据展示；它们不改变 G10 的行为。

### 图层 (Graph Layer)

从 `depends_on` 构建有向的制品依赖图。边的方向是制品指向依赖项，例如 `claim -> dependency`。图层会检测缺失的依赖、有向环，以及依赖于草稿或其他预先接受的制品的已接受（accepted）制品。

### 验证层 (Verification Layer)

运行验证器适配器（verifier adapters）并规范化验证结果。可选的外部工具必须保持为可选的；缺少的工具应当产生被跳过（skipped）的验证器结果，而不是使核心系统崩溃。Python 检查器适配器运行本地代码库的检查器脚本。当受支持的后端可用时，SAT 适配器通过一个最小的可选 DIMACS CNF 调用路径进行支持，同时保持 SAT 求解器二进制文件为可选的，并在没有可用后端时记录被跳过的结果。SMT 适配器同样通过支持的后端（当前在可用时为外部的 `z3`）支持最小的可选 SMT-LIB 调用路径，保持求解器二进制文件可选，在没有后端时记录被跳过的结果。Lean 适配器通过支持的后端（当前在可用时为外部的 `lean`）支持最小的可选纯 Lean 文件调用路径，保持 Lean 为可选的，并在没有后端时记录被跳过的结果。没有验证器适配器会执行自然语言自动形式化（autoformalization）。Lean 适配器不会提取或检查记录在 `formalizations` 中的 CSLib/mathlib 引用。

### 门禁/审查层 (Gate/Review Layer)

将模式检查、代码库不变量、依赖项检查、验证器结果、可重复性元数据、来源元数据以及 PR 检查表检查组合为门禁结果（gate results）。

对齐审查与验证器执行保持分离。缺少可选的 Lean 工具仍然产生被跳过的验证器结果，而不是通过（pass）。门禁层通过模式/模型验证和 G10 静态元数据验证记录形式链接字段。当策略元数据不一致时，G10 可能会阻断常规的 gatekeeper 运行，这意味着通过现有的 gatekeeper 阻断问题机制，阻断了晋升为 accepted 状态。它并未添加新的晋升策略路径。

具备工作区感知（Workspace-aware）的依赖检查会额外拒绝依赖于私有制品的公开制品。状态/路径检查会相对于每个配置的 KB 根目录评估制品生命周期路径，因此 `kb/public/accepted/...` 和 `kb/private/accepted/...` 在各自的根目录内都使用 accepted 路径的语义。

### 智能体套件层 (Agent Harness Layer)

为 Codex 和其他智能体构建有边界的上下文包（context packs），记录任务假设，并保持任务执行锚定于代码库文件而不是对话状态。

当前的智能体套件输出为：
- `context/TASKS/<issue-id>/` 上下文包。
- `.cosheaf/tasks/<task-id>.yaml` 运行时任务记录。
- `.cosheaf/tasks/<task-id>/runs/<run-id>/` 具有单独 stdout 和 stderr 文件的本地工作器（worker）运行记录。

上下文包使用确定性的相关性排序。排名包括直接的 Issue 制品引用、一跳（one-hop）的依赖邻居、与 Issue 文本或标签匹配的制品领域，以及与 Issue 标签匹配的制品标签。列出的每个制品都包含可解释的排序原因。在同一个相关性类别中，优先考虑 accepted 的制品而不是 draft 制品。被反驳、过时和被取代的制品仅在相关时包含在内，并被标记为已知的失败项，而非当前真理。

当一个相关的制品携带形式链接元数据或策略相关的形式设置时，上下文包中将包含紧凑的 formalization、alignment、verification policy 以及 G10 相关的提示行。这些行仅是切换（handoff）时的元数据：它们不会加载门禁报告，不代表当前的 G10 裁决，也不声称进行了 Lean 验证。

任务套件仅定义协议级别的工作器类型。创建、列出或完成任务不会调用 LLM 或外部服务。编排器存根（orchestrator stub）验证任务是否在 Issue 范围内，记录确定性的默认任务 ID，并且只有在本地工作器输出的包通过了工作器契约检查之后才能将任务标记为已完成。

本地工作器运行器不是一个 LLM 运行时或模型提供商集成。它仅以 `shell=False` 的方式执行明确的 argv 命令，默认其工作目录为代码库根目录，拒绝位于代码库之外的工作目录，在执行命令前拒绝位于代码库之外的包路径，强制执行超时，捕获 stdout 和 stderr，并在任务的 `.cosheaf` 运行目录中写入确定性的运行记录。可选的包处理会在命令执行完毕后验证工作器输出包；它不会合并输出或晋升为 accepted 知识。

工作器输出包（Worker output bundles）是本地的 YAML 清单。制品和审查输出必须引用通过了现有模式门禁的本地代码库 YAML 记录。包清单也可以作为包含 `bundle.yaml` 的本地代码库目录进行传递。包绝不能指向 `kb/accepted/`，任务的完成并不会将任何内容合并到 accepted 知识中。

### CLI 层 (CLI Layer)

提供用于验证、门禁执行、图检查、上下文生成、工作区检查、生命周期制品写入和调用验证器的公共命令。

生命周期写入命令是具有工作区感知的。在配置的工作区中，`cosheaf artifact create` 默认写入可写的私有 KB 根目录，而 `cosheaf artifact move-status` 拒绝修改从只读 KB 根目录加载的记录。

## 模块依赖方向

预期的模块依赖方向为：
```text
core -> config -> storage -> graph -> gates -> verification -> agent -> cli
```
低层模块不得导入高层模块。公开接口的变更必须记录在 `context/INTERFACE_REGISTRY.md` 中。

## 确定性

对于相同的代码库状态和工具可用性，索引、生成的输出、上下文包和门禁报告必须是确定性的。

## 架构决策

架构决策必须使用 ADR 格式记录在 `docs/ADR/` 下。
