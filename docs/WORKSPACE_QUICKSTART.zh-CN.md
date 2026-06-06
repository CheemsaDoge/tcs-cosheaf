[中文版](WORKSPACE_QUICKSTART.zh-CN.md) | [English](WORKSPACE_QUICKSTART.md)

# 工作区快速入门 (Workspace Quickstart)

本指南展示了在使用框架包、公开知识库（public KB）以及私有研究一起时的推荐端到端工作区形态。

## 推荐的布局

`tcs-cosheaf` 是运行时包。它被安装到 Python 环境中，不应当被复制进研究工作区中。

一种实用的工作区布局如下：

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

使用这种布局时，将公开 KB 的根目录配置到公开 KB 的子树中：

```toml
[workspace]
name = "my-tcs-workspace"

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

[policy]
private_can_depend_on_public = true
public_can_depend_on_private = false
accepted_requires_source = true
```

工作区模板默认使用较短的 `kb/public` 路径。如果将 `kb/public` 替换为或挂载为公开 KB 的内容，那么这也是有效的。

```text
workspace/
|-- cosheaf.toml
`-- kb/
    |-- public/
    `-- private/
```

在上述两种布局中，公开的 KB 根目录对于下游的工作区而言是只读的，而私有的 KB 根目录是可写的。

## 安装运行时

将框架包安装到活动的（active）环境中：

```bash
python -m pip install "git+https://github.com/CheemsaDoge/tcs-cosheaf.git@v0.1.1"
```

如果是进行框架开发，请单独克隆 `tcs-cosheaf` 并在其中安装开发依赖。切勿将框架签出的代码本身变成用户的私有研究工作区。

## 验证

在工作区的根目录下，检查活动的根目录并运行正常的本地检查：

```bash
cosheaf workspace info
cosheaf validate
cosheaf gate run
cosheaf index rebuild
```

预期的依赖方向是：

```text
private artifact -> public artifact
```

公开制品不得依赖于私有制品。已接受的（accepted）制品不得依赖草稿（draft）或其他被预先接受的制品，即使是跨越不同 KB 根目录也是如此。

## 常见的工作流

1. 将私有或实验性材料起草于 `kb/private/` 之下。
2. 保持猜想、失败的尝试、未发表的想法以及本地研究笔记私有。
3. 从工作区根目录运行 validate（验证）、gatekeeper（门禁）以及 context-pack（上下文包）命令。
4. 只有当制品满足代码库策略时，再对其进行审查并晋升。
5. 将可复用的公开材料通过一个独立的且经过来源审查的公开 KB Issue 和 Pull Request，转移到 `tcs-kb-public`。
6. 使公开的 KB 在下游工作区中保持只读挂载状态。

## 公开知识策略

公开知识库存储库旨在用于可复用的、可被引用的知识制品。它们不应包含私有猜想、未发表的研究想法，或是未经人类审查的被 LLM 生成并接受的制品。

被接受（accepted）的公开制品要求提供来源元数据并经过人工审查。公开 KB 中的证明草图是起说明作用并经过来源审查的制品，它们不是经过机器检查的证明，也不是 Lean 的验证证据。

## 从传统布局迁移

早期的单一代码库工作区可能只包含：

```text
workspace/
`-- kb/
```

推荐的布局将私有工作与只读的公开知识相分离：

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

迁移步骤：

1. 添加一个包含一个只读公开根目录和一个可写私有根目录的 `cosheaf.toml`。
2. 将私有的草稿、猜想、实验和未经审查的材料移动到 `kb/private/` 之下，并在它们的生命周期状态已经符合策略时，保留诸如 `draft/` 和 `accepted/` 等子目录。
3. 将 `tcs-kb-public` 挂载或克隆为只读的公开根目录。
4. 不要将私有的已接受制品复制到公开 KB 中。可重用的公开材料应当在 `tcs-kb-public` 之中通过另一个经过审查的 PR 提出。
5. 在依赖迁移后的工作区之前，运行 `cosheaf workspace info`、`cosheaf validate`、`cosheaf gate run` 和 `cosheaf index rebuild`。

如果代码库中没有 `cosheaf.toml`，Cosheaf 会保留在 `kb/` 下包含一个可写 KB 根目录的传统模式。