from __future__ import annotations

from bible_skill.skill_template import render_skill


def test_skill_export_mentions_local_first_exact_commands() -> None:
    text = render_skill("./example-data")

    assert "Use installed local translation data first" in text
    assert "bible-skill installed --data-dir ./example-data" in text
    assert "bible-skill search QUERY --data-dir ./example-data" in text
    assert "bible-skill query TRANSLATION_ID REFERENCE --data-dir ./example-data" in text
    assert "bible-skill query TRANSLATION_ID REFERENCE --data-dir ./example-data --usfm" in text
    assert (
        "bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir ./example-data --markdown" in text
    )
    assert "bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir ./example-data --csv" in text
    assert "bible-skill download TRANSLATION_ID --data-dir ./example-data" in text
