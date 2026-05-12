[English](README.md) | [中文](README-zh.md) | [日本語](README-ja.md)

# Bible Skill

Bible Skill 是一个采用 MIT 许可证的 Python CLI 和可复用 AI Agent 技能，用于确定性查询圣经经文。它通过已下载的译本数据和精确的本地引用解析，帮助 Agent 避免不准确的经文引用和幻觉式经文出处，而不是依赖模型记忆。

此包尚未发布到任何包注册表。请仅从源码检出目录使用。

## 问题和动机

LLM 通常大致知道圣经内容，但可能混合不同译本、漏字、引用错误范围，或生成并不存在的措辞。Bible Skill 为 Agent 提供可重复的工作流：发现译本、下载允许使用的译本、列出本地数据，并精确查询用户要求的书卷、章节、经文或范围。

## 功能

- 从 Free Use Bible API 发现可用译本。
- 将完整译本下载到本地数据目录。
- 列出已安装译本，并显示书卷、章节和经文数量。
- 按书卷、章节、单节、节范围和同一书卷跨章范围查询本地经文。
- 以文本、JSON 或 Markdown 对比两个或更多已安装译本中的同一段本地经文。
- 在未下载整本译本时，使用 bible-api.com 作为精确经文查询的实时后备。
- 为 AI Agent 工作流导出 Hermes 兼容的 `SKILL.md`。

## 安装

克隆源码仓库：

```sh
git clone https://github.com/codecat-ai/bible-skill.git
cd bible-skill
python -m bible_skill.cli --help
```

如需在源码检出目录测试本地命令入口，请在你自己的虚拟环境中以可编辑模式安装此检出目录：

```sh
python -m pip install -e .
bible-skill --help
```

不要使用 `pip install bible-skill`、`uvx bible-skill` 或类似注册表安装命令；目前还没有注册表发布版本。

## 快速开始

```sh
bible-skill translations --query web
bible-skill download web --data-dir ./data
bible-skill installed --data-dir ./data
bible-skill query web "John 3:16" --data-dir ./data
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --json
bible-skill compare "John 3:16" web kjv --data-dir ./data --json
bible-skill compare "John 3:16" web kjv --data-dir ./data --markdown
bible-skill live "John 3:16" --translation web
bible-skill skill --data-dir ./data > skills/bible-skill/SKILL.md
```

## 引用精度

本地查询支持：

- 整卷：`John`
- 章节：`John 3`
- 单节：`John 3:16`
- 同章范围：`John 3:16-18`
- 同一书卷跨章范围：`John 3:16-4:2`
- USFM 书卷 ID：`JHN 3:16`

## 配置

使用 `--data-dir` 指定下载译本的保存位置。未指定时，Bible Skill 会使用适合平台的用户数据目录。下载记录会包含译本元数据、来源 URL、获取时间戳，以及提供方给出的许可证 URL。`compare` 命令只读取已安装的本地译本，因此比较前需要先下载每个译本。

## 数据和许可证

Bible Skill 不在此仓库中包含圣经文本。用户需要自行遵守译本条款。实时后备仅使用 bible-api.com 进行精确查询；不要从 bible-api.com 批量下载整本圣经。

## 开发

运行时代码使用 Python 3.11+ 和标准库，包括用 `urllib` 实现 HTTP 客户端。测试使用极小的人工夹具文本，而不是圣经文本。

在已准备好的开发环境中运行检查：

```sh
ruff check .
ruff format --check .
pytest -q
python -m build
```

## 测试

测试套件覆盖引用解析、本地经文查询和对比、Free Use Bible API 响应规范化、提供方端点、存储/下载行为、CLI 输出和生成的技能文本。

## 路线图

- 支持更多提供方数据结构和 USFM 导出。
- 增加已安装译本的本地元数据搜索。
- 在人工注册表验证后准备打包发布。

## 贡献

欢迎贡献。请保持改动小而清晰、用行为测试保护，并尊重译本许可证。参见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

MIT。参见 [LICENSE](LICENSE)。

本项目在 AI 辅助下维护，但项目行为会通过测试和源码审查验证。
