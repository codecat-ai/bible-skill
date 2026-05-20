# Bible Skill

Use installed local translation data first for exact Scripture lookup. Do not quote from memory when a local query can answer the request.

## Commands

- List installed translations: `bible-skill installed --data-dir DATA_DIR`
- Validate installed translation cache files: `bible-skill validate --data-dir DATA_DIR`
- Inspect a portable local cache manifest: `bible-skill cache manifest --data-dir DATA_DIR --json`
- Dry-run invalid cache cleanup: `bible-skill cache prune --data-dir DATA_DIR --json`
- Remove invalid cache directories after review: `bible-skill cache prune --data-dir DATA_DIR --yes`
- Search installed translation metadata: `bible-skill search QUERY --data-dir DATA_DIR`
- Query exact local passages: `bible-skill query TRANSLATION_ID REFERENCE --data-dir DATA_DIR`
- Export an exact local passage as Markdown for notes: `bible-skill query TRANSLATION_ID REFERENCE --data-dir DATA_DIR --markdown`
- Export an exact local passage as minimal USFM-like text: `bible-skill query TRANSLATION_ID REFERENCE --data-dir DATA_DIR --usfm`
- Include local translation license/source metadata in exported local passages: `bible-skill query TRANSLATION_ID REFERENCE --data-dir DATA_DIR --markdown --attribution`
- Compare an exact passage across local translations: `bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir DATA_DIR`
- Export a comparison as Markdown for notes or agent context: `bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir DATA_DIR --markdown`
- Export a comparison as CSV for spreadsheets: `bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir DATA_DIR --csv`
- Include per-translation license/source metadata in local comparisons: `bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir DATA_DIR --csv --attribution`
- Extract references from notes or sermons: `bible-skill extract --text "See John 3:16 and Romans 8:28-30"`
- Extract references from a local Markdown file as JSON: `bible-skill extract --file notes.md --json`
- Export extracted references from a local Markdown file as Markdown: `bible-skill extract --file notes.md --markdown`
- Export extracted references from a local Markdown file as CSV: `bible-skill extract --file notes.md --csv`
- List downloadable translations: `bible-skill translations`
- Download an allowed translation: `bible-skill download TRANSLATION_ID --data-dir DATA_DIR`
- Use live fallback only when local data is unavailable: `bible-skill live "John 3:16" --translation web`
- Set live fallback timeout and bounded transient retries for automation: `bible-skill live "John 3:16" --translation web --timeout 10 --retries 2`
- Export a live fallback passage as Markdown for notes: `bible-skill live "John 3:16" --translation web --markdown`
- Export a live fallback passage as CSV for spreadsheets: `bible-skill live "John 3:16" --translation web --csv`

## Offline Source-Checkout Setup

Use this skill from a trusted source checkout; it is not a package-registry install path.
Create and activate a local virtual environment in the checkout, then install the checkout in editable mode with development dependencies:

- `python -m venv .venv`
- `source .venv/bin/activate`
- `uv pip install -e '.[dev]'`
- `bible-skill validate --data-dir DATA_DIR`
- `bible-skill skill --data-dir DATA_DIR > skills/bible-skill/SKILL.md`

Point the agent at the generated SKILL.md and keep the same `--data-dir` in every local lookup command. Validate the local data directory before use, prefer installed translations, and disable live fallback unless the task explicitly permits network use.

## Operating Rules

Prefer local installed data, cite the returned normalized reference and translation id, and preserve exact wording from the tool output. Respect translation metadata and license URLs.
Use local `--attribution` when outputs need translation license or source URLs.
Use `bible-skill cache manifest --json` before transferring a cache between machines; re-run `bible-skill validate` after transfer and treat manifest `issues` as automation failure signals.
Run `bible-skill validate --data-dir DATA_DIR` before relying on cached local translations in automated workflows; it checks `translation.json` and sidecar `metadata.json` for malformed metadata, checksum drift, and metadata mismatches. Use `--json` when callers need machine-readable issue lists.
When validation reports corruption, inspect `bible-skill cache manifest --data-dir DATA_DIR --json`, run `bible-skill cache prune --data-dir DATA_DIR --json` as a dry-run, then rerun with `--yes` only after confirming the invalid translation IDs. Re-download removed translations before querying them.
Live `--json` output is raw provider JSON. Live Markdown and CSV renderers also tolerate provider responses wrapped in a top-level `data` object, `verses` or `passages` lists, and verse text stored as `text`, `content`, `verse_text`, or nested mixed fragments.
Unsupported live provider schemas fail with diagnostics for missing `reference`, malformed `data`, malformed `verses` or `passages`, and missing verse text. These schema failures are not retryable and do not show the live retry hint.
Use live `--timeout SECONDS` and `--retries COUNT` only for bounded provider calls; semantic provider responses such as 404/no passage found are not retried.
Live provider HTTP errors include the status, useful provider error text when available, and `Retry-After` backoff hints when returned.
When a live network or transient HTTP provider failure happens without requested retries, CLI stderr suggests retrying with `--retries 2`; unsupported provider schema and invalid JSON failures do not get that hint.
