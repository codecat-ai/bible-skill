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
        f"- Query exact local passages: `bible-skill query TRANSLATION_ID REFERENCE --data-dir {data_dir}`",
        "- Compare an exact passage across local translations: "
        f"`bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir {data_dir}`",
        "- Export a comparison as Markdown for notes or agent context: "
        f"`bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir {data_dir} --markdown`",
        "- List downloadable translations: `bible-skill translations`",
        f"- Download an allowed translation: `bible-skill download TRANSLATION_ID --data-dir {data_dir}`",
        '- Use live fallback only when local data is unavailable: `bible-skill live "John 3:16" --translation web`',
        "",
        "## Operating Rules",
        "",
        "Prefer local installed data, cite the returned normalized reference and translation id, and preserve exact "
        "wording from the tool output. Respect translation metadata and license URLs.",
        "",
    ]
    return "\n".join(lines)
