# Bible Skill

Use installed local translation data first for exact Scripture lookup. Do not quote from memory when a local query can answer the request.

## Commands

- List installed translations: `bible-skill installed --data-dir DATA_DIR`
- Validate installed translation cache files: `bible-skill validate --data-dir DATA_DIR`
- Search installed translation metadata: `bible-skill search QUERY --data-dir DATA_DIR`
- Query exact local passages: `bible-skill query TRANSLATION_ID REFERENCE --data-dir DATA_DIR`
- Export an exact local passage as Markdown for notes: `bible-skill query TRANSLATION_ID REFERENCE --data-dir DATA_DIR --markdown`
- Export an exact local passage as minimal USFM-like text: `bible-skill query TRANSLATION_ID REFERENCE --data-dir DATA_DIR --usfm`
- Compare an exact passage across local translations: `bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir DATA_DIR`
- Export a comparison as Markdown for notes or agent context: `bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir DATA_DIR --markdown`
- Export a comparison as CSV for spreadsheets: `bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir DATA_DIR --csv`
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

## Operating Rules

Prefer local installed data, cite the returned normalized reference and translation id, and preserve exact wording from the tool output. Respect translation metadata and license URLs.
Run `bible-skill validate --data-dir DATA_DIR` before relying on cached local translations in automated workflows; use `--json` when callers need machine-readable issue lists.
Live `--json` output is raw provider JSON. Live Markdown and CSV renderers also tolerate provider responses wrapped in a top-level `data` object, `verses` or `passages` lists, and verse text stored as `text`, `content`, `verse_text`, or nested mixed fragments.
Use live `--timeout SECONDS` and `--retries COUNT` only for bounded provider calls; semantic provider responses such as 404/no passage found are not retried.
Live provider HTTP errors include the status, useful provider error text when available, and `Retry-After` backoff hints when returned.
