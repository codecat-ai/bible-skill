from __future__ import annotations


def render_skill(data_dir: str) -> str:
    lines = [
        "# Bible Skill",
        "",
        "Use installed local translation data first for exact Scripture lookup. Do not quote from memory when a local "
        "query can answer the request.",
        "",
        "## Commands",
        "",
        f"- List installed translations: `bible-skill installed --data-dir {data_dir}`",
        f"- Validate installed translation cache files: `bible-skill validate --data-dir {data_dir}`",
        f"- Inspect a portable local cache manifest: `bible-skill cache manifest --data-dir {data_dir} --json`",
        f"- Dry-run invalid cache cleanup: `bible-skill cache prune --data-dir {data_dir} --json`",
        f"- Remove invalid cache directories after review: `bible-skill cache prune --data-dir {data_dir} --yes`",
        f"- Search installed translation metadata: `bible-skill search QUERY --data-dir {data_dir}`",
        f"- Query exact local passages: `bible-skill query TRANSLATION_ID REFERENCE --data-dir {data_dir}`",
        "- Export an exact local passage as Markdown for notes: "
        f"`bible-skill query TRANSLATION_ID REFERENCE --data-dir {data_dir} --markdown`",
        "- Export an exact local passage as minimal USFM-like text: "
        f"`bible-skill query TRANSLATION_ID REFERENCE --data-dir {data_dir} --usfm`",
        "- Include local translation license/source metadata in exported local passages: "
        f"`bible-skill query TRANSLATION_ID REFERENCE --data-dir {data_dir} --markdown --attribution`",
        "- Compare an exact passage across local translations: "
        f"`bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir {data_dir}`",
        "- Export a comparison as Markdown for notes or agent context: "
        f"`bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir {data_dir} --markdown`",
        "- Export a comparison as CSV for spreadsheets: "
        f"`bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir {data_dir} --csv`",
        "- Include per-translation license/source metadata in local comparisons: "
        f"`bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir {data_dir} --csv "
        "--attribution`",
        '- Extract references from notes or sermons: `bible-skill extract --text "See John 3:16 and Romans 8:28-30"`',
        "- Extract references from a local Markdown file as JSON: `bible-skill extract --file notes.md --json`",
        "- Export extracted references from a local Markdown file as Markdown: "
        "`bible-skill extract --file notes.md --markdown`",
        "- Export extracted references from a local Markdown file as CSV: `bible-skill extract --file notes.md --csv`",
        "- List downloadable translations: `bible-skill translations`",
        f"- Download an allowed translation: `bible-skill download TRANSLATION_ID --data-dir {data_dir}`",
        '- Use live fallback only when local data is unavailable: `bible-skill live "John 3:16" --translation web`',
        "- Set live fallback timeout and bounded transient retries for automation: "
        '`bible-skill live "John 3:16" --translation web --timeout 10 --retries 2`',
        "- Export a live fallback passage as Markdown for notes: "
        '`bible-skill live "John 3:16" --translation web --markdown`',
        "- Export a live fallback passage as CSV for spreadsheets: "
        '`bible-skill live "John 3:16" --translation web --csv`',
        "",
        "## Offline Source-Checkout Setup",
        "",
        "Use this skill from a trusted source checkout; it is not a package-registry install path.",
        "Create and activate a local virtual environment in the checkout, then install the checkout in editable mode "
        "with development dependencies:",
        "",
        "- `python -m venv .venv`",
        "- `source .venv/bin/activate`",
        "- `uv pip install -e '.[dev]'`",
        f"- `bible-skill validate --data-dir {data_dir}`",
        f"- `bible-skill skill --data-dir {data_dir} > skills/bible-skill/SKILL.md`",
        "",
        "Point the agent at the generated SKILL.md and keep the same `--data-dir` in every local lookup command. "
        "Validate the local data directory before use, prefer installed translations, and disable live fallback unless "
        "the task explicitly permits network use.",
        "",
        "## Operating Rules",
        "",
        "Prefer local installed data, cite the returned normalized reference and translation id, and preserve exact "
        "wording from the tool output. Respect translation metadata and license URLs.",
        "Use local `--attribution` when outputs need translation license or source URLs.",
        "Use `bible-skill cache manifest --json` before transferring a cache between machines; re-run "
        "`bible-skill validate` after transfer and treat manifest `issues` as automation failure signals.",
        "Run `bible-skill validate --data-dir DATA_DIR` before relying on cached local translations in automated "
        "workflows; it checks `translation.json` and sidecar `metadata.json` for malformed metadata, checksum "
        "drift, and metadata mismatches. Use `--json` when callers need machine-readable issue lists.",
        "When validation reports corruption, inspect `bible-skill cache manifest --data-dir DATA_DIR --json`, run "
        "`bible-skill cache prune --data-dir DATA_DIR --json` as a dry-run, then rerun with `--yes` only after "
        "confirming the invalid translation IDs. Re-download removed translations before querying them.",
        "Live `--json` output is raw provider JSON. Live Markdown and CSV renderers also tolerate provider responses "
        "wrapped in a top-level `data` object, `verses` or `passages` lists, and verse text stored as `text`, "
        "`content`, `verse_text`, or nested mixed fragments.",
        "Use live `--timeout SECONDS` and `--retries COUNT` only for bounded provider calls; semantic provider "
        "responses such as 404/no passage found are not retried.",
        "Live provider HTTP errors include the status, useful provider error text when available, and `Retry-After` "
        "backoff hints when returned.",
        "When a live network or transient HTTP provider failure happens without requested retries, CLI stderr suggests "
        "retrying with `--retries 2`; unsupported provider schema and invalid JSON failures do not get that hint.",
    ]
    return "\n".join(lines)
