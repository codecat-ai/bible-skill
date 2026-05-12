# Bible Skill clean-room brief

## Project summary
Bible Skill is an MIT-licensed open-source project that packages a reusable AI-agent skill plus a small Python CLI for reliable Bible passage lookup. It helps agents avoid hallucinated or imprecise Scripture quotations by using downloaded translation data and deterministic passage parsing instead of relying on model memory.

## Target users and situations
- AI agent maintainers who want a drop-in skill for Scripture lookup in research, writing, pastoral-study, literature-analysis, or educational workflows.
- Developers building assistants that need exact Bible quotes by book/chapter/verse/range.
- Multilingual users who need to compare public-domain/free-use translations without manually navigating APIs.

## Problem
LLMs often know Bible text broadly, but may quote wording inaccurately, mix translations, invent verse ranges, or cite the wrong chapter/verse. A dedicated skill with local downloaded translation JSON can make lookup deterministic, inspectable, and reusable.

## Non-goals and boundaries
- Do not provide theological interpretation or claim doctrinal authority.
- Do not bypass API/license restrictions. Store translation metadata and license URLs; users must respect translation terms.
- Do not bulk-download from bible-api.com because its docs warn not to download entire Bibles from that service. Use bible-api.com only for live passage queries and translation listing.
- Prefer Free Use Bible API (https://bible.helloao.org/) for translation list and complete translation downloads because it documents a complete translation endpoint.
- Do not include copyrighted Bible text in this repository.

## Stack decision
Use Python 3.11+ for a portable CLI, testable parsing/query logic, and simple packaging. Provide a generated Hermes-style `skills/bible-skill/SKILL.md` template that tells agents how to use the CLI. No registry install commands until published; document clone/local usage only.

## MVP features and acceptance criteria
1. Translation discovery
   - `bible-skill translations` fetches or reads cached translation metadata.
   - Supports filtering by language/name/id with `--query` and `--language`.
   - Output is readable text by default and JSON with `--json`.
2. Translation download/save
   - `bible-skill download TRANSLATION_ID` downloads a complete translation from Free Use Bible API and stores it under an app data directory or `--data-dir`.
   - Saves metadata, source URL, fetched timestamp, and license URL.
   - `--force` refreshes an existing translation; without `--force` it reuses existing data.
3. View downloaded translations
   - `bible-skill installed` lists locally saved translations with book/chapter/verse counts and metadata.
4. Deterministic passage lookup from local data
   - `bible-skill query TRANSLATION_ID REFERENCE` supports book, book chapter, single verse, chapter verse ranges, and same-book cross-chapter ranges where data exists.
   - Examples: `John`, `John 3`, `John 3:16`, `John 3:16-18`, `John 3:16-4:2`, `JHN 3:16`.
   - Supports common English book names, numeric book names (`1 John`), and USFM IDs (`JHN`).
   - Text output includes translation id and normalized references. JSON output is machine-readable.
5. Live fallback query
   - `bible-skill live "John 3:16" --translation web` queries bible-api.com for a precise passage without downloading a full Bible.
6. Skill export
   - `bible-skill skill --data-dir ...` prints a Hermes-compatible `SKILL.md` that instructs AI agents to use installed local data first, list translations, download allowed translations, and query exact passages.
7. Error handling
   - Clear messages for unknown translation, missing local translation, unknown book, invalid reference syntax, out-of-range chapter/verse, and network/API failures.

## Expected architecture
- `bible_skill/books.py`: canonical Protestant 66-book metadata, aliases, OSIS/USFM IDs.
- `bible_skill/references.py`: reference parser and normalized passage ranges.
- `bible_skill/store.py`: data-directory layout and installed translation metadata.
- `bible_skill/providers.py`: Free Use Bible API and bible-api.com clients using stdlib urllib.
- `bible_skill/query.py`: deterministic local passage selection and rendering.
- `bible_skill/cli.py`: argparse CLI.
- `bible_skill/skill_template.py`: generated agent skill Markdown.
- `tests/`: behavior-first tests with fixtures, no live network required for core tests.

## Data model expectations
Free Use Bible API complete translation JSON may include translation metadata and books with chapters/verses. Implement tolerant normalization for common shapes using fixtures. Core query tests should use a small local fixture with Genesis, John, and 1 John-like aliases.

## TDD test scenarios
- RED tests for parsing book/chapter/verse/ranges including `John 3:16-18`, `John 3:16-4:2`, `1 John 1:1`, and invalid references.
- RED tests for querying a fixture by whole book, chapter, single verse, and range.
- RED tests for local store installed listing and download skip/force behavior with mocked provider functions.
- RED tests for CLI JSON output and friendly errors.
- RED tests that skill export mentions exact commands and local-first behavior.

## Required repository files
- README.md (English), README-zh.md, README-ja.md with synchronized meaning and top language switcher.
- LICENSE (MIT), CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md.
- `.github/workflows/ci.yml`, issue templates, PR template.
- `.gitignore`, `pyproject.toml` with dev dependencies (`pytest`, `ruff`, `build`).

## Verification
- `uv venv --python 3.11 .venv`
- `. .venv/bin/activate && uv pip install -e '.[dev]'`
- `ruff check .`
- `ruff format --check .`
- `pytest -q`
- `python -m build`
- CLI smoke tests against fixture/local temp data and live translation-list fallback where safe.

## README truthfulness
Document local source checkout usage only. Do not claim PyPI/uvx/pip install from registry. Mention that package-registry publishing is not available yet.

## Roadmap
- More robust support for additional API data shapes and USFM exports.
- Optional side-by-side multi-translation comparison output.
- Packaged release after manual approval and registry verification.
