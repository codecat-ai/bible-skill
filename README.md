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
- Validate installed translation cache files for required metadata, book/chapter/verse structure, non-empty verse text, and deterministic checksums.
- Search installed translation metadata locally by id, name, language, license URL, or source URL.
- Query local passages by book, chapter, single verse, verse range, and same-book cross-chapter range.
- Extract Bible references from arbitrary notes, sermons, or Markdown using the same local parser and book data.
- Export local query results as minimal deterministic USFM-like text.
- Compare the same local passage across two or more installed translations in text, JSON, Markdown, or CSV.
- Use bible-api.com as a live fallback for precise passage queries without downloading a whole Bible, with text, raw JSON, Markdown, or CSV output and configurable timeout/retry settings.
- Report live provider HTTP failures with useful provider messages, compact body excerpts, and `Retry-After` backoff hints when available.
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
bible-skill validate --data-dir ./data
bible-skill validate web --data-dir ./data --json
bible-skill search english --data-dir ./data
bible-skill search license.example --data-dir ./data --json
bible-skill query web "John 3:16" --data-dir ./data
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --json
bible-skill query web "JHN 3:16-4:2" --data-dir ./data --usfm
bible-skill compare "John 3:16" web kjv --data-dir ./data --json
bible-skill compare "John 3:16" web kjv --data-dir ./data --markdown
bible-skill compare "John 3:16" web kjv --data-dir ./data --csv
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

## Reference precision

Local queries accept:

- whole book: `John`
- chapter: `John 3`
- single verse: `John 3:16`
- same-chapter range: `John 3:16-18`
- same-book cross-chapter range: `John 3:16-4:2`
- USFM book IDs: `JHN 3:16`

## Reference extraction

Use `bible-skill extract` to scan notes, sermons, or Markdown before querying or comparing passages. `--text TEXT` and `--file PATH` are mutually exclusive, and one is required. Text output prints one de-duplicated normalized reference per line, preserving first appearance order. `--json` emits rows with matched text, normalized reference, offsets, book id/name, and start/end chapter and verse fields. `--markdown` emits a note-friendly summary headed `# Extracted Bible references`, with each normalized reference in bold and escaped source context when matches exist, or `No Bible references found.` when none do. `--csv` emits spreadsheet-friendly rows with `reference`, `book`, `chapter`, `start_verse`, `end_verse`, `start`, `end`, and `context` columns; empty results still print only the header row. `--json`, `--markdown`, and `--csv` are mutually exclusive.

The pure Python API is available as `bible_skill.extract.extract_references(text)` for agent and application workflows. Extraction recognizes the same book names, aliases, and USFM IDs accepted by `parse_reference`, including forms such as `John 3:16`, `JHN 3:16-4:2`, `Genesis 1`, and `Romans 8:28-30`.

## Configuration

Use `--data-dir` to choose where downloaded translations are saved. Without it, Bible Skill uses a platform-appropriate user data directory. Downloaded records include translation metadata, source URL, fetched timestamp, license URL when the provider supplies it, and a deterministic `sha256:` checksum calculated from normalized translation content without the fetched timestamp. The `validate` command checks installed cache files before agents rely on them; pass optional translation IDs to validate only those caches, or omit IDs to validate every installed translation. Text output is tab-separated and concise, while `--json` emits objects with `translation_id`, `ok`, `checksum`, and `issues`. Validation exits non-zero if any requested cache is missing or invalid. The `search` and `compare` commands read only installed local translations, so download each translation before searching local metadata or comparing passages.

The live fallback supports `--json` for the raw provider response, `--markdown` for note-friendly output, and `--csv` for spreadsheet-friendly rows with `reference`, `translation`, `verse_reference`, and `text` columns. `--json`, `--markdown`, and `--csv` are mutually exclusive. Use `--timeout SECONDS` to change the provider request timeout from the default 30 seconds, and `--retries COUNT` to retry transient network errors or transient HTTP responses such as 408, 429, and 5xx responses. The default retry count is 0, so existing single-attempt behavior is preserved unless retries are requested. Semantic provider responses such as 404/no passage found are not retried. Markdown and CSV rendering remains compatible with bible-api.com-shaped payloads, and also tolerates provider payloads wrapped in a top-level `data` object, verse lists named `verses` or `passages`, and verse text stored as `text`, `content`, `verse_text`, or nested arrays/objects. Nested fragments are joined with readable spacing. When a live provider returns an HTTP error, CLI stderr includes the status, a readable provider error field or short normalized plain-text body when available, and any `Retry-After` value.

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

The test suite covers reference parsing, local metadata search, local passage lookup, cache checksum validation, USFM export and comparison exports, Free Use Bible API response normalization, provider endpoints, timeout/retry behavior and error fixtures, store/download behavior, CLI output, and generated skill text.

## Roadmap

- Prepare a packaged release after manual registry verification.

## Contributing

Contributions are welcome. Please keep changes small, behavior-tested, and respectful of translation licenses. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

This project is maintained with AI assistance, but project behavior is verified with tests and source review.
