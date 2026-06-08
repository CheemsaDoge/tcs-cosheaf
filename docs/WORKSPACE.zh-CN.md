[中文版](WORKSPACE.zh-CN.md) | [English](WORKSPACE.md)

# 工作区模型 (Workspace Model)

TCS-Cosheaf 工作区由位于代码库根目录的一个可选文件 `cosheaf.toml` 进行配置。如果该文件不存在，命令将保留传统的单一代码库行为，并在 `kb/` 加载一个可写的 KB 根目录。

## 推荐的三存储库设置

框架存储库是 `tcs-cosheaf`。它提供了 CLI、模式（schemas）、门禁（gates）、验证（validation）、验证器适配器以及智能体套件。它不被推荐作为放置普通用户私有研究笔记的地方。

可复用的公开知识库是 [`tcs-kb-public`](https://github.com/CheemsaDoge/tcs-kb-public)。下游的用户工作区应当将它作为只读的公开 KB 根目录进行挂载。

推荐给用户的入口是 [`tcs-cosheaf-workspace-template`](https://github.com/CheemsaDoge/tcs-cosheaf-workspace-template)。该模板结合了框架包、一个只读的公开 KB 根目录以及一个可写的 `kb/private` 叠加层。用户不应当手动将框架代码库和 KB 代码库合并成一个临时（ad hoc）的树结构。

预期的依赖方向是：

```text
private user artifact -> public KB artifact
```

公开的 KB 制品不得依赖于私有制品。当 `[policy] private_can_depend_on_public = true` 时，私有叠加层可以依赖于公开制品。

有关简短的端到端设置指南，请参阅 [`docs/WORKSPACE_QUICKSTART.md`](WORKSPACE_QUICKSTART.md)。

## 配置

当前工作区配置的形态如下：

```toml
[workspace]
name = "my-tcs-workspace"

[[kb]]
name = "public"
path = "kb/public"
readonly = true
priority = 10

[[kb]]
name = "private"
path = "kb/private"
readonly = false
priority = 20

[policy]
private_can_depend_on_public = true
public_can_depend_on_private = false
accepted_requires_source = true
```

每个 KB 根目录包含：
- `name`：用于报告和加载记录元数据中的稳定的根目录名称。
- `path`：相对于代码库的工作区 KB 根目录路径。
- `readonly`：写命令是否可以修改该根目录。
- `priority`：确定性的排序和报告优先级。

绝对路径和父目录遍历是被拒绝的。KB 的根名称和路径必须唯一。

## 命令行为

当 `cosheaf.toml` 存在时，下列命令默认使用它：
- `cosheaf validate`
- `cosheaf gate` 与 `cosheaf gate run`
- `cosheaf context build` 与 `cosheaf context show`
- `cosheaf index rebuild`
- `cosheaf graph show`
- `cosheaf artifact create`
- `cosheaf artifact move-status`
- `cosheaf workspace info`

`cosheaf workspace info` 打印活动模式（active mode）、代码库根目录和 KB 根目录。

当配置的工作区同时拥有只读和可写的根目录时，创建制品的操作默认会写入到可写的私有根目录中。状态移动命令会拒绝修改从只读根目录中加载的记录。

`cosheaf artifact promote <artifact-id>` 同样拒绝只读的 KB 根目录。如果为了便于维护使公开的 KB 根目录变为可写，且 `[policy] accepted_requires_source` 为 true，那么晋升（promote）操作会拒绝那些尚未附带完整结构化来源元数据的公开制品。

## 查询 SQLite 索引

`cosheaf index rebuild` 会从当前的 YAML 记录写入 `.cosheaf/index.sqlite`。YAML 仍然是事实来源，因此调用方在更改代码库后、使用查询 API 之前，应当重新构建索引。

最小的 Python 用法示例：

```python
from cosheaf.storage.index import rebuild_index
from cosheaf.storage.query import ArtifactIndexQuery
from cosheaf.storage.repo import RepoContext

context = RepoContext(".")
rebuild_index(context)

query = ArtifactIndexQuery.from_context(context)
all_artifacts = query.list_artifacts()
drafts = query.list_artifacts_by_status("draft")
graph_artifacts = query.list_artifacts_by_domain("graph-theory")
deps = query.list_dependencies("claim.example")
rdeps = query.list_reverse_dependencies("definition.graph")
```

每个制品行包含了 `kb_root`，其值可能是 `public`、`private`、`default`，如果索引的记录并非来自 KB 根目录，则为空字符串。

## 分层规则

加载的记录会保留它们的来源 KB 根目录名称、根路径、只读标志以及相对于该根目录的路径。验证与门禁会强制要求：
- 跨所有根目录，制品 ID 必须全局唯一。
- 私有制品可以依赖公开制品。
- 公开制品不得依赖私有制品。
- 已接受（accepted）的制品不能依赖草稿或预先接受的制品，即使是跨 KB 根目录也是如此。
- 当 `accepted_requires_source = true` 时，公开 KB 根目录中被接受的制品必须包含完整的结构化来源元数据。
- 在当前策略下，只有公开的草稿制品和私有的被接受制品不会仅因缺少来源元数据而被阻断。
- 状态/路径规则是相对于每个 KB 根目录评估的。
- 诸如创建等生命周期写命令不能修改只读根目录。

## 传统模式

在没有 `cosheaf.toml` 的情况下，活动的 KB 根目录为：

```text
default | kb | readonly=false | priority=0
```

这保留了对现有用户和测试而言的单一代码库行为。传统模式下没有配置的公开 KB 根目录，因此针对 accepted 公开来源元数据的门禁会报告为 `not_applicable`（不适用）。

## 从传统布局迁移

传统的代码库通常具有一个单一的可写 KB 根目录：

```text
workspace/
`-- kb/
```

推荐的工作区布局将用户私有的材料与只读的公开知识相分离：

```text
workspace/
|-- cosheaf.toml
|-- kb/
|   `-- private/
`-- external/
    `-- tcs-kb-public/
        `-- kb/
            `-- public/
```

使用一个经过配置的公开根目录，例如：

```toml
[[kb]]
name = "public"
path = "external/tcs-kb-public/kb/public"
readonly = true
priority = 10

[[kb]]
name = "private"
path = "kb/private"
readonly = false
priority = 20
```

当 `kb/public` 路径被替换为或从公开 KB 的内容进行挂载时，工作区模板中默认的 `kb/public` 根目录也是有效的。

迁移应保留制品的意义和状态。将私有草稿、猜想、失败的尝试、实验以及未发表的笔记移动到 `kb/private/` 之下。切勿将私有材料复制到公开的 KB 根目录中。可复用的公开制品应当通过一个独立的并且经过来源审查的 Issue 和 Pull Request，向 `tcs-kb-public` 提出。

迁移后，运行：

```bash
cosheaf workspace info
cosheaf validate
cosheaf gate run
cosheaf index rebuild
```