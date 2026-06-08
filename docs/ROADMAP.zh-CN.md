[中文版](ROADMAP.zh-CN.md) | [English](ROADMAP.md)

# 路线图

TCS-Cosheaf 正在准备 v0.1.1 形式化链接层（Formal Link Layer）支持版本，同时仍处于 pre-MVP 阶段。此路线图是有意具体化的，与命名的里程碑或活跃的 GitHub issue 相挂钩。它不应被解读为对日期、采用情况或生产就绪状态的承诺。

## 当前里程碑：v0.1.1 形式化链接层支持

目标：在形式化链接层元数据、G10 静态元数据验证、上下文包展示、确定性索引存储和只读查询 API 落地后，为框架打上标签（tag），同时保留仅限元数据的边界。

已完成的脚手架部分包括：

- 类型化制品模型和初始模式（schemas）。
- 由文件系统支持的制品加载和确定性的 YAML 写入。
- 代码库验证 CLI。
- 针对非已接受状态转换的制品创建和生命周期状态变更 CLI。
- 受控的接受制品晋升工作流。
- 依赖图和确定性的索引重建输出。
- 通过 `ArtifactIndexQuery` 对重建的索引输出提供只读的 SQLite 查询 API，包括制品、状态、类型、领域、依赖、反向依赖、形式化和形式化策略查询。
- 包含机器可读 JSON 和人类可读 Markdown 的关卡报告。
- 针对明确的 PR 正文 markdown 文件的本地 G8 PR 检查清单关卡。
- 针对 issue 作用域的代理任务排序后的上下文包生成。
- 形式化链接层制品字段 `formalizations`、`alignment` 和 `verification_policy`。
- 用于形式化链接元数据、对齐审查和验证策略之间静态一致性的 G10 形式化链接关卡。
- 不声称 Lean 验证的上下文包形式化链接展示。
- 确定性的 `formalizations` 和 `artifact_formal_policy` SQLite 表。
- 本地任务、worker 契约和协调器存根。
- 验证器适配器协议、Python 检查器适配器、最小可选的 SAT DIMACS 适配器、最小可选的 SMT-LIB 适配器和最小可选的 Lean 纯文件适配器。
- 针对可执行证据验证器结果的再现性元数据关卡。
- 分支保护和审查策略文档。
- 第一个带有草稿制品证据和本地 Python 检查器的图论试验工作流。
- 第二个带有可选 SAT 证据和 Python 备用检查器的 SAT/CNF 试验工作流。
- GitHub Actions CI 和协作模板。

## 活跃 Issues

实时的 issue 状态在 GitHub issues 中跟踪。此路线图记录持久的方向和命名的里程碑；它不应用于作为手动维护的当前未解决 issue 列表。

## 下一个命名里程碑

### MVP 易用性

- 改善托管 PR 工作流的 PR 检查清单人体工程学，不使本地关卡依赖于 GitHub API 访问。

### 验证深度

- 为记录的 `import_path` 和 `symbol` 元数据添加外部 Lean 库引用检查，而不打包引入（vendoring）CSLib 或 mathlib。
- 扩展 SAT 后端覆盖范围，超越最小可选的 DIMACS 调用路径。
- 扩展 SMT 后端覆盖范围，超越最小可选的 SMT-LIB 调用路径。
- 扩展 Lean 支持，超越最小可选的纯文件调用路径。
- 保持所有外部形式化工具为可选；不可用的工具必须产生跳过的验证器结果。

### 查询和审查易用性

- 改善制品搜索和图检查工作流。
- 如果用户需要非 Python 的检查流程，在现有的 `ArtifactIndexQuery` Python API 之上添加面向 CLI 的查询易用性。

## MVP 的非目标

- Web UI。
- 模型训练。
- 自动定理证明代理。
- 完整的 Lean 自动形式化。
- CSLib/mathlib 的替代或引入（vendoring）。
- 自动的非形式化/形式化语义对齐检查。
- 多用户权限系统。
- 有关项目采用情况、生产使用、用户、标星或下载量的声明。
