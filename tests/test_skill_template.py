from __future__ import annotations

from bible_skill.skill_template import render_skill


def test_skill_export_mentions_local_first_exact_commands() -> None:
    text = render_skill("./example-data")

    assert "Use installed local translation data first" in text
    assert "bible-skill installed --data-dir ./example-data" in text
    assert "bible-skill validate --data-dir ./example-data" in text
    assert "bible-skill search QUERY --data-dir ./example-data" in text
    assert "bible-skill query TRANSLATION_ID REFERENCE --data-dir ./example-data" in text
    assert "bible-skill query TRANSLATION_ID REFERENCE --data-dir ./example-data --usfm" in text
    assert (
        "bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir ./example-data --markdown" in text
    )
    assert "bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir ./example-data --csv" in text
    assert 'bible-skill extract --text "See John 3:16 and Romans 8:28-30"' in text
    assert "bible-skill extract --file notes.md --json" in text
    assert "bible-skill extract --file notes.md --markdown" in text
    assert "bible-skill extract --file notes.md --csv" in text
    assert "bible-skill download TRANSLATION_ID --data-dir ./example-data" in text
    assert 'bible-skill live "John 3:16" --translation web --timeout 10 --retries 2' in text
    assert 'bible-skill live "John 3:16" --translation web --markdown' in text
    assert 'bible-skill live "John 3:16" --translation web --csv' in text
    assert "Live `--json` output is raw provider JSON." in text
    assert "Live provider HTTP errors include the status" in text
    assert "use `--json` when callers need machine-readable issue lists" in text
    assert "top-level `data` object" in text
    assert "`content`, `verse_text`, or nested mixed fragments" in text
    assert "Use live `--timeout SECONDS` and `--retries COUNT` only for bounded provider calls" in text
