[中文版](FORMALIZATION_LINKS.zh-CN.md) | [English](FORMALIZATION_LINKS.md)

# 形式化链接

## 目的

形式化链接层允许制品（artifact）指向外部 Lean 库（如 CSLib 或 mathlib）中的形式化声明。它是引用的元数据层，而不是证明导入层，也不能替代这些库。

Cosheaf 仍然是一个由 Git 支持的研究知识库和工作流框架。它不打包引入（vendor）CSLib、mathlib 或 Lean 证明，也不试图在制品的 YAML 中重建它们的库生态系统。

## 制品字段

制品现在可以包含：

- `formalizations`: 对外部形式化声明的引用。
- `alignment`: 非形式化陈述与形式化声明之间语义对齐的审查元数据。
- `verification_policy`: 每个制品的策略，描述是否预期存在形式化链接、Lean 检查或对齐审查。

这些字段是可选的。省略它们的现有制品仍然有效。

## 形式化引用

每个 `formalizations` 条目记录一个完整的声明引用：

- `id`: 链接的稳定本地标识符。
- `system`: 目前为 `lean4`。
- `library`: 源库名称，例如 `CSLib` 或 `mathlib`。
- `library_ref`: 库级别的引用，如模块、包、提交（commit）或目录键。
- `import_path`: Lean 导入路径。
- `symbol`: 声明名称。
- `declaration_kind`: `definition`、`theorem`、`lemma`、`instance`、`structure` 或 `other`。
- `status`: `planned`、`linked`、`checked`、`broken` 或 `deprecated`。
- `check_mode`: `external_library_ref` 或 `local_file`。
- `expected_type`: 可选的预期 Lean 类型或简短的类型摘要。
- `notes`: 可选的审查者或维护者注释。

YAML 存储这些引用，而不是 Lean 证明主体。不得将 `formalizations` 条目用作粘贴库证明的地方。链接 ID 使用与制品 ID 相同的以点分隔的小写连字符（slug）格式。去除空白后，`library`、`library_ref`、`import_path` 和 `symbol` 必须非空。

## 对齐审查

Lean 可以检查形式化声明，但 Lean 通过并不自动证明非形式化制品陈述与该声明在语义上是对齐的。对齐审查是一个独立的人工或维护者审查步骤。

`alignment` 对象记录：

- `status`: `none`、`requested`、`human_reviewed` 或 `rejected`。
- `reviewer`: 适用时的审查者标识符。
- `reviewed_at`: 包含时区的审查时间戳或 `null`。
- `convention_notes`: 约定不匹配或需要检查的假设。
- `limitations`: 对齐声明中已知的差距。

状态 `human_reviewed` 和 `rejected` 要求审查者非空。`reviewed_at` 如果存在，必须包含时区信息。

例如，一个图论定理可能取决于非形式化陈述与 Lean 声明之间的自环、平行边、有限图或图同构约定是否匹配。

## 验证策略

`verification_policy` 对象记录当前的期望：

- `source_reviewed`: 源元数据和普通审查已足够。
- `source_reviewed_with_formal_link`: 制品应带有形式化链接，但该链接不一定在 CI 中被检查。
- `machine_checked`: 预期有可执行证据或验证器输出。
- `lean_required`: 针对需要 Lean 检查的制品的未来策略级别。

布尔字段 `require_formal_link`、`require_lean_check` 和 `require_alignment_review` 明确声明了对每个制品的期望。
`source_reviewed_with_formal_link` 要求 `require_formal_link: true`。
`lean_required` 要求同时满足 `require_formal_link: true` 和 `require_lean_check: true`。

这些策略值会经过模式（schema）验证，也会由 G10 形式化链接关卡（Formal Link Gate）检查以保证静态元数据的一致性。当缺少所需的形式化链接、Lean 检查或对齐审查时，G10 会提供普通的关卡拦截问题。除了现有的拦截性关卡问题会阻止晋升（promotion）这一规则外，它不改变接受晋升的策略。

## 与证据的关系

外部库引用不得存储在现有的 `evidence` 字段中。`evidence` 仍用于存储本地代码库的可执行证据、外部证据路径和验证器输入。形式化声明引用属于 `formalizations`，以便审查者区分引用、形式化链接、对齐和可执行检查等概念。

## Lean 适配器边界

当前的 Lean 验证器适配器仅支持通过本地可用的 `lean` 命令进行可选的纯 Lean 文件检查。它不将 Lean、CSLib、mathlib 或 lake 作为依赖项添加。它不获取外部库，也不需要网络访问。

当可选的 Lean 工具不可用时，Lean 验证保持为 `skipped`（跳过），而不是 `pass`（通过）。跳过的验证器输出不得用于声称形式化检查成功。

形式化链接层不会使 Lean 适配器检查外部库引用。它只记录链接，以便未来的工具和审查工作流具有稳定的元数据表面。

## G10 形式化链接关卡

G10 是一个针对 `formalizations`、`alignment` 和 `verification_policy` 的静态元数据关卡。它不执行 Lean、不安装 CSLib 或 mathlib、不获取外部库，也不需要网络访问。

当制品的策略要求形式化链接、Lean 检查或对齐审查，而相应的元数据缺失或未经过审查时，G10 会拦截该制品。对于要求形式化链接且对齐被拒绝的已接受制品，如果其仅有的形式化结果是 `broken` 或 `deprecated`，G10 也会拦截。

G10 警告是非拦截性的，且不是证明失败。警告会突出显示需要注意的元数据，例如已接受制品上的计划形式化、已接受制品上请求的对齐审查、没有验证器证据链接的已检查外部库引用，或策略未要求但存在的形式化链接。

## 上下文包

如果存在形式化元数据或与策略相关，问题作用域内的上下文包（Context Packs）将包含相关制品的紧凑形式化链接摘要。摘要显示形式化声明引用、对齐状态、验证策略以及与 G10 相关的静态提示，例如需要形式化链接、需要 Lean 检查、需要对齐审查、对齐被拒绝或计划的形式化。

这种展示仅限于元数据。它可以帮助代理（agents）看到形式化链接的表面，但它不会加载关卡报告，不会声称当前的 G10 判定结果，也不会表示 Lean 已经验证了非形式化制品。

## SQLite 索引和查询 API

`cosheaf index rebuild` 将形式化链接元数据写入生成的索引输出中：

- `.cosheaf/index.sqlite` 的 `formalizations` 表
- `.cosheaf/index.sqlite` 的 `artifact_formal_policy` 表
- 每个制品的 `.cosheaf/artifact_manifest.json` 形式化、对齐状态和验证策略字段

SQLite 查询 API 可以按制品、库、符号、状态或导入路径列出形式化结果，并可以列出需要形式化链接、Lean 检查或对齐审查的策略行。查询 API 是只读的：它读取已存在的 `.cosheaf/index.sqlite` 文件，不会隐式重建索引。

这些索引和查询表面保持仅为元数据级别。它们不检查 CSLib 或 mathlib 符号是否存在，不获取外部库，也不运行 Lean。

## 未来工作

- 使用 `import_path` 和 `symbol` 进行外部 Lean 库引用检查。
- 具有计划的或已审查的形式化链接的公共 KB 制品。
- 未来的 `LeanLibraryRefAdapter` 或等效的检查器表面。

## 当前限制

- 不添加 CSLib 或 mathlib 依赖。
- 不需要或使用网络访问。
- 不检查外部 Lean 库的检出。
- 不实现自然语言的自动形式化。
- 不实现自动的非形式化/形式化对齐证明。
- G10 仅限元数据，不执行 Lean。
- 索引/查询支持仅限元数据，不执行 Lean 或库的存在性检查。
- 上下文包的展示仅限元数据，不声称 Lean 验证结果。
- 除了正常的关卡拦截行为外，不增加已接受晋升策略的变更。
