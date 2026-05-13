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
        f"- Search installed translation metadata: `bible-skill search QUERY --data-dir {data_dir}`",
        f"- Query exact local passages: `bible-skill query TRANSLATION_ID REFERENCE --data-dir {data_dir}`",
        "- Export an exact local passage as minimal USFM-like text: "
        f"`bible-skill query TRANSLATION_ID REFERENCE --data-dir {data_dir} --usfm`",
        "- Compare an exact passage across local translations: "
        f"`bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir {data_dir}`",
        "- Export a comparison as Markdown for notes or agent context: "
        f"`bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir {data_dir} --markdown`",
        "- Export a comparison as CSV for spreadsheets: "
        f"`bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir {data_dir} --csv`",
        '- Extract references from notes or sermons: `bible-skill extract --text "See John 3:16 and Romans 8:28-30"`',
        "- Extract references from a local Markdown file as JSON: `bible-skill extract --file notes.md --json`",
        "- Export extracted references from a local Markdown file as Markdown: "
        "`bible-skill extract --file notes.md --markdown`",
        "- Export extracted references from a local Markdown file as CSV: `bible-skill extract --file notes.md --csv`",
        "- List downloadable translations: `bible-skill translations`",
        f"- Download an allowed translation: `bible-skill download TRANSLATION_ID --data-dir {data_dir}`",
        '- Use live fallback only when local data is unavailable: `bible-skill live "John 3:16" --translation web`',
        "- Export a live fallback passage as Markdown for notes: "
        '`bible-skill live "John 3:16" --translation web --markdown`',
        "- Export a live fallback passage as CSV for spreadsheets: "
        '`bible-skill live "John 3:16" --translation web --csv`',
        "",
        "## Operating Rules",
        "",
        "Prefer local installed data, cite the returned normalized reference and translation id, and preserve exact "
        "wording from the tool output. Respect translation metadata and license URLs.",
        "Live `--json` output is raw provider JSON. Live Markdown and CSV renderers also tolerate provider responses "
        "wrapped in a top-level `data` object, `verses` or `passages` lists, and verse text stored as `text`, "
        "`content`, `verse_text`, or nested mixed fragments.",
        "Live provider HTTP errors include the status, useful provider error text when available, and `Retry-After` "
        "backoff hints when returned.",
        "",
    ]
    return "\n".join(lines)
