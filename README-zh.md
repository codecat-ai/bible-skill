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
- 验证已安装译本缓存文件的必需元数据、旁路元数据一致性、书卷/章节/经文结构、非空经文文本和确定性校验和。
- 检查可移植缓存清单，包含译本元数据、POSIX 风格相对路径、校验和、数量统计和供传输自动化使用的验证问题。
- 按 ID、名称、语言、许可证 URL 或来源 URL 在本地搜索已安装译本的元数据。
- 按书卷、章节、单节、节范围和同一书卷跨章范围查询本地经文。
- 使用同一个本地解析器和书卷数据，从任意笔记、讲章或 Markdown 中提取圣经引用。
- 将本地查询结果导出为适合笔记的 Markdown 或最小、确定性的类 USFM 文本，并可选择包含本地译本归属信息。
- 以文本、JSON、Markdown 或 CSV 对比两个或更多已安装译本中的同一段本地经文。
- 在未下载整本译本时，使用 bible-api.com 作为精确经文查询的实时后备，并支持文本、原始 JSON、Markdown 或 CSV 输出以及可配置的超时/重试设置。
- 在实时提供方返回 HTTP 失败时，报告有用的提供方消息、简短正文摘录、可用的 `Retry-After` 退避提示，以及一时性失败的重试建议。
- 在任何手动发布前检查源码检出目录的打包和文档就绪状态，且不会发布，也不会声明注册表安装可用。
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
python -m venv .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
bible-skill --help
```

不要使用 `pip install bible-skill`、`uvx bible-skill` 或类似注册表安装命令；目前还没有注册表发布版本。

## 离线/仅本地 Agent 设置

离线或仅本地 Agent 工作应使用可信的源码检出目录。请在允许使用网络时准备或刷新允许使用的本地译本数据，然后先验证这些数据，再交给 Agent 使用：

```sh
git clone https://github.com/codecat-ai/bible-skill.git
cd bible-skill
python -m venv .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
bible-skill translations --query web
bible-skill download web --data-dir ./data
bible-skill validate --data-dir ./data
bible-skill cache manifest --data-dir ./data --json
bible-skill cache prune --data-dir ./data --json
bible-skill installed --data-dir ./data
bible-skill skill --data-dir ./data > skills/bible-skill/SKILL.md
```

将 Agent 指向生成的 `skills/bible-skill/SKILL.md`，并在本地查询命令中保持使用 `--data-dir ./data`。优先使用已安装译本，并保留工具返回的原文、规范化引用、译本 ID 和归属元数据。除非任务明确允许网络使用，否则禁用实时后备。

## 快速开始

```sh
bible-skill translations --query web
bible-skill download web --data-dir ./data
bible-skill installed --data-dir ./data
bible-skill validate --data-dir ./data
bible-skill validate web --data-dir ./data --json
bible-skill cache manifest --data-dir ./data --json
bible-skill cache prune --data-dir ./data --json
bible-skill cache prune web --data-dir ./data --yes
bible-skill search english --data-dir ./data
bible-skill search license.example --data-dir ./data --json
bible-skill query web "John 3:16" --data-dir ./data
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --json
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --markdown
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --markdown --attribution
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --usfm
bible-skill compare "John 3:16" web kjv --data-dir ./data --json
bible-skill compare "John 3:16" web kjv --data-dir ./data --markdown
bible-skill compare "John 3:16" web kjv --data-dir ./data --csv
bible-skill compare "John 3:16" web kjv --data-dir ./data --csv --attribution
bible-skill extract --text "Discuss John 3:16 and Romans 8:28-30."
bible-skill extract --text "Discuss John 3:16 and Romans 8:28-30." --markdown
bible-skill extract --file sermon-notes.md --json
bible-skill extract --file sermon-notes.md --markdown
bible-skill extract --file sermon-notes.md --csv
bible-skill live "John 3:16" --translation web
bible-skill live "John 3:16" --translation web --timeout 10 --retries 2
bible-skill live "John 3:16" --translation web --markdown
bible-skill live "John 3:16" --translation web --csv
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

## 引用提取

在查询或对比经文前，可以用 `bible-skill extract` 扫描笔记、讲章或 Markdown。`--text TEXT` 和 `--file PATH` 互斥，且必须提供其中一个。文本输出会按首次出现顺序，每行打印一个去重后的规范化引用。`--json` 会输出多行对象，包含匹配文本、规范化引用、字符偏移、书卷 ID/名称，以及起止章节和经文字段。`--markdown` 会输出以 `# Extracted Bible references` 开头、适合笔记粘贴的摘要；有匹配时，每条使用加粗的规范化引用和已转义的来源上下文，没有匹配时输出 `No Bible references found.`。`--csv` 会输出适合电子表格的行，列为 `reference`、`book`、`chapter`、`start_verse`、`end_verse`、`start`、`end` 和 `context`；没有匹配时只打印标题行。`--json`、`--markdown` 与 `--csv` 互斥。

纯 Python API 可通过 `bible_skill.extract.extract_references(text)` 使用，适合 Agent 和应用工作流。提取功能识别与 `parse_reference` 相同的书卷名称、别名和 USFM ID，包括 `John 3:16`、`JHN 3:16-4:2`、`Genesis 1` 和 `Romans 8:28-30` 等形式。

## 配置

使用 `--data-dir` 指定下载译本的保存位置。未指定时，Bible Skill 会使用适合平台的用户数据目录。下载记录会包含译本元数据、来源 URL、获取时间戳、提供方给出的许可证 URL，以及一个从规范化译本内容计算的确定性 `sha256:` 校验和；获取时间戳不会纳入校验和。`validate` 命令会在 Agent 依赖缓存前检查已安装的 `translation.json` 及其旁路 `metadata.json` 文件；可以传入可选译本 ID 只验证这些缓存，也可以省略 ID 验证所有已安装译本。它会报告缺失或格式错误的旁路元数据、旁路校验和漂移，以及旁路元数据与译本文元数据之间的不一致。文本输出简洁且以制表符分隔，`--json` 会输出包含 `translation_id`、`ok`、`checksum` 和 `issues` 的对象。如果任何请求的缓存缺失或无效，验证会以非零状态退出。

在不同机器或 Agent 工作区之间传输本地缓存前，可以运行 `bible-skill cache manifest --data-dir ./data --json`。该清单只是检查辅助信息，不是包或注册表声明：它会报告 `schema_version`、`generated_at`、`data_dir`，并为每个缓存目录列出 id、名称、语言、许可证/来源 URL、书卷/章节/经文数量、校验和、POSIX 风格 `relative_path`、`validation_ok` 和 `issues`。自动化流程可以复制数据目录，比较传输前后的清单，然后在目标位置运行 `bible-skill validate --data-dir ./data`。缺失或损坏的缓存文件，包括格式错误的旁路元数据，会尽可能以问题列表表示，而不是让整个清单生成失败。当验证报告损坏时，先检查清单，再运行默认 dry-run 的 `bible-skill cache prune --data-dir ./data --json`，审查后再运行 `bible-skill cache prune TRANSLATION_ID --data-dir ./data --yes`，或省略 ID 删除所有无效缓存目录。JSON prune 输出包含 `schema_version`、`dry_run`、`removed_count`、`removed`、`kept` 和 `issues`；有效条目永远不会被删除，请求的缺失 ID 会作为问题报告且不会删除无关条目。查询前请重新下载已删除的译本。`search` 和 `compare` 命令只读取已安装的本地译本，因此搜索本地元数据或比较经文前需要先下载每个译本。

本地 `query` 默认输出文本，`--json` 输出机器可读的经文对象，`--markdown` 输出以规范化引用和译本 ID 为标题、适合笔记粘贴的 Markdown，`--usfm` 输出最小、确定性的类 USFM 文本。`--json`、`--markdown` 与 `--usfm` 互斥。在本地 `query` 或 `compare` 导出中传入 `--attribution`，会包含可用的 `license_url` 和 `source_url` 元数据。JSON 只在请求时添加结构化 `attribution` 对象；compare CSV 会添加稳定的 `license_url` 和 `source_url` 列。

实时后备支持用 `--json` 输出原始提供方响应，用 `--markdown` 输出适合粘贴到笔记中的文本，也支持用 `--csv` 输出适合电子表格的行，列为 `reference`、`translation`、`verse_reference` 和 `text`。`--json`、`--markdown` 与 `--csv` 互斥。使用 `--timeout SECONDS` 可从默认 30 秒调整提供方请求超时，使用 `--retries COUNT` 可重试一时性网络错误或 408、429、5xx 等一时性 HTTP 响应。默认重试次数为 0，因此除非显式请求重试，否则仍保持单次尝试行为。实时网络失败或一时性 HTTP 提供方失败在默认重试次数下发生时，CLI stderr 会建议尝试 `--retries 2`；不支持的提供方结构和无效 JSON 失败不会显示该提示。404/no passage found 等语义性提供方响应不会重试。Markdown 和 CSV 渲染保持兼容 bible-api.com 形状的载荷，也容忍包在顶层 `data` 对象中的提供方载荷、名为 `verses` 或 `passages` 的经文列表，以及存放在 `text`、`content`、`verse_text` 或嵌套数组/对象中的经文文本。嵌套片段会用可读间距连接。当实时提供方返回 HTTP 错误时，CLI stderr 会包含状态码、可读取的提供方错误字段或简短规范化的纯文本正文，并包含任何 `Retry-After` 值。

## 数据和许可证

Bible Skill 不在此仓库中包含圣经文本。用户需要自行遵守译本条款。实时后备仅使用 bible-api.com 进行精确查询；不要从 bible-api.com 批量下载整本圣经。

## 开发

运行时代码使用 Python 3.11+ 和标准库，包括用 `urllib` 实现 HTTP 客户端。测试使用极小的人工夹具文本，而不是圣经文本。

在源码检出目录中使用 `bible-skill release check` 检查打包元数据、顶层 README/LICENSE 文件、MIT 许可证文本、存在 `dist/` 时的构建产物元数据，以及 README 变体中未验证的注册表安装声明。它只是发布前就绪检查；不会发布任何内容，也不会验证包注册表可用性。使用 `--json` 可在 stdout 输出可解析的自动化结果，使用 `--dist-dir PATH` 可检查指定的产物目录。

在已准备好的开发环境中运行检查：

```sh
ruff check .
ruff format --check .
pytest -q
bible-skill release check --json
python -m build
```

## 测试

测试套件覆盖引用解析、本地元数据搜索、本地经文查询、缓存校验和及旁路元数据验证、缓存清单检查、无效缓存修剪、本地 Markdown 与 USFM 导出、对比导出、发布就绪检查、Free Use Bible API 响应规范化、提供方端点、超时/重试行为、重试提示、网络/HTTP 错误夹具、存储/下载行为、CLI 输出和生成的技能文本。

## 路线图

Bible Skill 目前按成长项目跟踪，节奏为每周 1 次聚焦维护会话。完整的完成度复核、维护触发条件和节奏规则见 [ROADMAP.md](ROADMAP.md)。

当前路线图重点：

- 使用 `bible-skill release check` 和构建产物评估第一个手动源码检出发布候选；在真实注册表发布经过验证前，不添加注册表安装命令。

## 贡献

欢迎贡献。请保持改动小而清晰、用行为测试保护，并尊重译本许可证。参见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

MIT。参见 [LICENSE](LICENSE)。

本项目在 AI 辅助下维护，但项目行为会通过测试和源码审查验证。
