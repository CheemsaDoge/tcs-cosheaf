[中文版](ARTIFACT_SCHEMA.zh-CN.md) | [English](ARTIFACT_SCHEMA.md)

# 研究制品模式 (Artifact Schema)

## 目的

本文档描述了研究制品的词汇、生命周期假设以及最初的机器可读模式文件。现阶段这些模式有意保持轻量：它们定义了文件级别的契约，由 Pydantic 模型层、代码库验证流程以及制品生命周期 CLI 命令进行强制约束。

## 计划中的研究制品类型

- `definition` (定义)：引入一个术语、对象、属性、模型或符号。
- `claim` (主张/论断)：陈述一个命题，该命题可能是不正式的、中间性的或有待进一步归类的。
- `theorem` (定理)：陈述一个被认为已获证明的主张。
- `conjecture` (猜想)：陈述一个被认为是合理但尚未证明的主张。
- `proof` (证明)：提供旨在确立定理、主张或构造属性的证据。
- `proof_attempt` (证明尝试)：记录部分、失败或探索性的证明路径。
- `construction` (构造)：描述从指定输入构建的数学或计算对象。
- `algorithm` (算法)：描述一个可执行或可分析的过程。
- `reduction` (归约)：描述问题、模型或制品陈述之间的归约关系。
- `counterexample` (反例)：记录反驳某一主张或对猜想施加限制的对象或论证。
- `experiment` (实验)：记录经验性、计算性或探索性的测试。
- `review` (审查)：记录人工或智能体的审查发现。
- `verifier` (验证器)：描述检查器、证明助手调用、脚本、SAT/SMT 查询或其他验证机制。
- `issue` (议题)：记录已知问题、未解决的问题、不一致或后续跟进事项。

## 计划中的公共字段

基础的制品模式当前定义了以下公共字段：

- `id`
- `type`
- `title`
- `domain`
- `status`
- `created_at`
- `updated_at`
- `authors`
- `depends_on`
- `supersedes`
- `tags`
- `statement`
- `evidence`
- `sources`
- `formalizations`
- `alignment`
- `verification_policy`
- `review`
- `risk`

## 来源元数据 (Source Metadata)

研究制品可以通过 `sources` 携带结构化的来源元数据。对于草案制品和传统的单根代码库，该字段是可选的。但对于配置了公共 KB 根目录中的已接受制品，当 `accepted_requires_source = true` 时，策略上要求必须提供。

每个来源条目支持：

- `kind`：`paper`、`book`、`survey`、`lecture_note`、`website`、`internal_note`，或者 `other`
- `title`
- `authors`
- `year`
- `doi`
- `arxiv`
- `url`
- `theorem_number`
- `page`
- `notes`

对于被接受的公共制品，至少需要提供一个来源，且每个来源必须包含非空的标题 (title)、至少一位作者 (author)、年份 (year)，以及至少一个来自 `doi`、`arxiv`、`url`、`theorem_number` 或 `page` 的引用定位符。`depends_on` 中的外部依赖引用不能替代来源元数据。

## 形式化链接 (Formalization Links)

制品可以通过 `formalizations` 携带形式化声明引用。这些引用指向外部的形式化库（如 CSLib 或 mathlib），而无需将证明主体复制到 YAML 中，也不会将这些库变成框架的依赖项。

每个形式化引用包括：

- `id`
- `system`：目前为 `lean4`
- `library`
- `library_ref`
- `import_path`
- `symbol`
- `declaration_kind`：`definition`、`theorem`、`lemma`、`instance`、`structure`，或者 `other`
- `status`：`planned`、`linked`、`checked`、`broken`，或者 `deprecated`
- `check_mode`：`external_library_ref` 或 `local_file`
- `expected_type`：可选，默认为空字符串
- `notes`：可选，默认为空字符串

形式化引用 ID 使用与制品 ID 相同的以点分隔的小写缩写形式。去除空格后，`library`、`library_ref`、`import_path` 和 `symbol` 必须为非空。

形式化声明引用不得存储在 `evidence` 中。`evidence` 字段依然用于可执行或类似证据的输入；形式化库的引用应属于 `formalizations`。

`alignment` 记录了非正式声明与形式化声明之间的语义审查。Lean 可以检查形式化文件或声明，但 Lean 验证通过并不能自动证明非正式的制品声明使用了相同的约定或陈述了相同的定理。对齐审查 (Alignment review) 独立于 Lean 检查。若存在 `reviewed_at`，它必须是时区感知的。`human_reviewed` 和 `rejected` 的对齐状态要求提供非空的审稿人 (reviewer)。

`verification_policy` 记录制品是否期望形式化链接、Lean 检查或对齐审查。目前的级别有 `source_reviewed`、`source_reviewed_with_formal_link`、`machine_checked` 和 `lean_required`。策略值经过 schema/model 验证，G10 也会静态检查该策略、`formalizations` 与 `alignment` 之间的一致性。G10 可以产生普通的阻塞性门控问题，因此对已接受状态的晋升，仅通过“阻塞性门控问题会阻止晋升”这一现有规则产生影响。`source_reviewed_with_formal_link` 要求 `require_formal_link: true`；`lean_required` 则同时要求 `require_formal_link: true` 和 `require_lean_check: true`。

## ID 格式

制品和议题 ID 是全局唯一、由点号分隔的标识符。第一段必须是一个小写短横线分隔词 (slug)。后续分段可以是小写词或者是例如 `0001` 这样的数字版本/索引段。

示例：

- `claim.example.complete-graph-edge-count`
- `construction.graph-toy.0001`
- `issue.graph-toy-search.0001`

本地的 `depends_on` 和 `supersedes` 条目使用同样的制品 ID 格式。`depends_on` 也可能包含以 `external:` 开头的显式外部引用。外部依赖引用不是本地制品 ID，不要求必须解析到本代码库中的文件。

## 状态值 (Status Values)

初始的制品状态值包括：

- `raw`
- `draft`
- `locally_tested`
- `adversarially_tested`
- `machine_checked`
- `human_reviewed`
- `accepted`
- `refuted`
- `obsolete`
- `superseded`

## 生命周期路径

生命周期路径规则是制品契约的一部分：

- `kb/draft/<type-plural>/<artifact-id>.yaml` 可能存储 `raw`、`draft`、`locally_tested`、`adversarially_tested`、`machine_checked`、`human_reviewed`、`refuted`、`obsolete` 或 `superseded` 制品。它永远不存储 `accepted` 制品。
- `kb/accepted/<type-plural>/<artifact-id>.yaml` 仅存储 `accepted` 制品。
- `kb/refuted/<artifact-id>.yaml` 仅存储 `refuted` 制品。
- `kb/obsolete/<artifact-id>.yaml` 仅存储 `obsolete` 或 `superseded` 制品。

生命周期 CLI 会根据制品类型、状态和 ID 推导出规范路径。默认情况下，草案和预接受制品会在 `kb/draft/` 下创建。将制品移动至 `refuted`、`obsolete` 或 `superseded` 时，它会被移动到终端状态区域。拒绝直接以 `accepted` 状态创建，也拒绝直接 `move-status ... accepted`。向“已接受”的晋升使用 `cosheaf artifact promote <artifact-id>`，而不是悄无声息的文件移动。

晋升过程会验证代码库，运行门控程序，拒绝目标验证器返回 `fail` 或 `error`，要求 `review.state` 为 `human_reviewed` 或 `accepted`，要求依赖项为本地的已接受制品或明确的外部引用，并将 `status` 更新为 `accepted`，刷新 `updated_at`，然后在 `kb/accepted/<type-plural>/<artifact-id>.yaml` 路径下写入确定性的 YAML 内容。

`review` 和 `issue` 记录具有单独的加载模型，并非供 `cosheaf artifact create` 或 `cosheaf artifact promote` 使用的生命周期制品记录。

## 内联审查状态 (Inline Review State)

制品的 `review.state` 当前接受：

- `none`
- `requested`
- `in_review`
- `approved`
- `changes_requested`
- `human_reviewed`
- `accepted`

只有 `human_reviewed` 和 `accepted` 才能满足“已接受制品”晋升的审查要求。

## 模式文件 (Schema Files)

最初的 JSON Schema 文件为：

- `schemas/artifact.schema.json`
- `schemas/issue.schema.json`
- `schemas/review.schema.json`
- `schemas/verifier.schema.json`

## Pydantic 模型 (Pydantic Models)

最初的 Pydantic v2 模型层存放在 `cosheaf/core/` 下：

- `cosheaf.core.artifact.BaseArtifact`
- `cosheaf.core.artifact.Evidence`
- `cosheaf.core.artifact.ReviewRef`
- `cosheaf.core.artifact.SourceMetadata`
- `cosheaf.core.artifact.FormalizationRef`
- `cosheaf.core.artifact.AlignmentReview`
- `cosheaf.core.artifact.VerificationPolicy`
- `cosheaf.core.artifact.Risk`
- `cosheaf.core.status.ArtifactType`
- `cosheaf.core.status.ArtifactStatus`

该模型层会验证制品 ID、枚举值、带时区感知的精确实间戳、依赖引用、证据记录、来源元数据结构、形式化链接结构、对齐审查状态、验证策略值、审查状态以及风险状态。
路径/状态规则作为纯辅助函数公开，它们不负责扫描代码库。

## 示例文件 (Example Files)

最初的 YAML 示例文件有：

- `examples/issues/issue.example.yaml`
- `examples/claims/claim.example.yaml`
- `examples/proofs/proof.example.yaml`
- `examples/constructions/graph.example.yaml`
- `examples/reviews/review.example.yaml`

## 当前实现状态 (Current Implementation Status)

目前已存在机器可读的 JSON Schema 文件，以及对应的示例 YAML 制品和初始 Pydantic v2 模型。已经实现了以下功能：基于文件系统的加载、代码库扫描、通过 `cosheaf validate` 进行的模式/模型验证、通过 `cosheaf artifact validate <path>` 进行的单文件验证、通过 `cosheaf artifact create` 确定性地创建制品、通过 `cosheaf artifact move-status` 安全地移至预接受或终端状态、通过 `cosheaf artifact promote` 晋升至已接受状态，以及通过 `cosheaf gate` 生成门控报告。可复现性元数据门控已针对可执行证据通过验证器结果元数据实现。直接以“已接受”状态创建以及直接执行 `move-status ... accepted` 仍然被阻止。G8 PR 检查清单约束可以通过 `cosheaf gate run --pr-checklist <path>` 验证本地 PR 正文 markdown 文件，若无检查清单来源则会被跳过。G9 来源元数据约束在配置了 `accepted_requires_source = true` 的工作区中会对被接受的公共制品进行检查，同时保留草案、私有与传统单根代码库的原始行为。

形式化链接层（Formal Link Layer）已作为可选的模式/模型元数据、示例制品、G10 静态元数据验证、上下文包展示和 SQLite/查询元数据面进行实现。它记录了 Lean 库中的声明引用，而不添加 CSLib/mathlib 依赖、不需要网络访问，也没有改变普通门控拦截之外的受接受制品晋升语义。G10 不执行 Lean，不获取或检查外部 Lean 库，也不会证明非正式与形式化语义的对齐。上下文包和查询 API 暴露相同的元数据，而不会声称 Lean 验证了非正式声明。此实现未增加形式化链接的 CLI 命令或针对外部库引用的验证器执行。