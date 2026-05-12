[English](README.md) | [中文](README-zh.md) | [日本語](README-ja.md)

# Bible Skill

Bible Skill is an MIT-licensed Python CLI and reusable AI-agent skill for deterministic Bible passage lookup. It helps agents avoid imprecise Scripture quotations and hallucinated citations by using downloaded translation data plus exact local reference parsing instead of model memory.

This package is not published to a package registry yet. Use it from a source checkout only.

## Problem and motivation

LLMs often know Bible passages broadly, but they can mix translations, omit words, cite the wrong range, or invent wording. Bible Skill gives an agent a repeatable workflow: discover translations, download an allowed translation, list local data, and query the requested book, chapter, verse, or range exactly.

## Features

- Discover available translations from Free Use Bible API.
- Download complete translations into a local data directory.
- List installed translations with book, chapter, and verse counts.
- Query local passages by book, chapter, single verse, verse range, and same-book cross-chapter range.
- Compare the same local passage across two or more installed translations in text or JSON.
- Use bible-api.com as a live fallback for precise passage queries without downloading a whole Bible.
- Export a Hermes-compatible `SKILL.md` for AI-agent workflows.

## Installation

Clone the source repository:

```sh
git clone https://github.com/codecat-ai/bible-skill.git
cd bible-skill
python -m bible_skill.cli --help
```

For local command entry point testing from a checkout, install this checkout in editable mode in your own virtual environment:

```sh
python -m pip install -e .
bible-skill --help
```

Do not use `pip install bible-skill`, `uvx bible-skill`, or similar registry commands; no registry release is available yet.

## Quick start

```sh
bible-skill translations --query web
bible-skill download web --data-dir ./data
bible-skill installed --data-dir ./data
bible-skill query web "John 3:16" --data-dir ./data
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --json
bible-skill compare "John 3:16" web kjv --data-dir ./data --json
bible-skill live "John 3:16" --translation web
bible-skill skill --data-dir ./data > skills/bible-skill/SKILL.md
```

## Reference precision

Local queries accept:

- whole book: `John`
- chapter: `John 3`
- single verse: `John 3:16`
- same-chapter range: `John 3:16-18`
- same-book cross-chapter range: `John 3:16-4:2`
- USFM book IDs: `JHN 3:16`

## Configuration

Use `--data-dir` to choose where downloaded translations are saved. Without it, Bible Skill uses a platform-appropriate user data directory. Downloaded records include translation metadata, source URL, fetched timestamp, and license URL when the provider supplies it. The `compare` command reads only installed local translations, so download each translation before comparing it.

## Data and licensing

Bible Skill does not include Bible text in this repository. Users are responsible for respecting translation terms. The live fallback uses bible-api.com for precise queries only; do not bulk-download entire Bibles from bible-api.com.

## Development

Runtime code uses Python 3.11+ and the standard library, including `urllib` for HTTP clients. Tests use tiny artificial fixtures rather than Bible text.

Run checks from a prepared development environment:

```sh
ruff check .
ruff format --check .
pytest -q
python -m build
```

## Testing

The test suite covers reference parsing, local passage lookup and comparison, Free Use Bible API response normalization, provider endpoints, store/download behavior, CLI output, and generated skill text.

## Roadmap

- Support more provider data shapes and USFM exports.
- Add export formats for comparison reports.
- Prepare a packaged release after manual registry verification.

## Contributing

Contributions are welcome. Please keep changes small, behavior-tested, and respectful of translation licenses. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

This project is maintained with AI assistance, but project behavior is verified with tests and source review.
