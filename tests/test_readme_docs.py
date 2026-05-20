from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_english_readme_documents_source_checkout_offline_agent_setup() -> None:
    text = _read("README.md")
    schema_diagnostic_text = (
        "missing `reference`, malformed `data`, malformed `verses` or `passages`, malformed verse entries, "
        "or missing verse text"
    )

    assert "## Offline/local-only agent setup" in text
    assert "python -m venv .venv" in text
    assert "uv pip install -e '.[dev]'" in text
    assert "bible-skill validate --data-dir ./data" in text
    assert "bible-skill cache manifest --data-dir ./data --json" in text
    assert "bible-skill cache prune --data-dir ./data --json" in text
    assert "bible-skill cache prune TRANSLATION_ID --data-dir ./data --yes" in text
    assert "bible-skill skill --data-dir ./data > skills/bible-skill/SKILL.md" in text
    assert "bible-skill release check --json" in text
    assert "pre-publish readiness check only" in text
    assert "Point the agent at the generated `skills/bible-skill/SKILL.md`" in text
    assert "Disable live fallback unless a task explicitly permits network use." in text
    assert "Do not use `pip install bible-skill`, `uvx bible-skill`, or similar registry commands" in text
    assert "suggests trying `--retries 2`" in text
    assert schema_diagnostic_text in text


def test_translated_readmes_document_matching_offline_agent_setup() -> None:
    zh = _read("README-zh.md")
    ja = _read("README-ja.md")

    for text in (zh, ja):
        assert "python -m venv .venv" in text
        assert "uv pip install -e '.[dev]'" in text
        assert "bible-skill validate --data-dir ./data" in text
        assert "bible-skill cache manifest --data-dir ./data --json" in text
        assert "bible-skill cache prune --data-dir ./data --json" in text
        assert "bible-skill cache prune TRANSLATION_ID --data-dir ./data --yes" in text
        assert "bible-skill skill --data-dir ./data > skills/bible-skill/SKILL.md" in text
        assert "bible-skill release check --json" in text
        assert "pip install bible-skill" in text
        assert "uvx bible-skill" in text
        assert "--retries 2" in text

    assert "## 离线/仅本地 Agent 设置" in zh
    assert "将 Agent 指向生成的 `skills/bible-skill/SKILL.md`" in zh
    assert "除非任务明确允许网络使用，否则禁用实时后备。" in zh
    assert "只是发布前就绪检查" in zh
    assert "缺少 `reference`、`data` 格式错误、`verses` 或 `passages` 格式错误、经文条目格式错误或缺少经文文本" in zh

    assert "## オフライン/ローカル専用 Agent セットアップ" in ja
    assert "生成した `skills/bible-skill/SKILL.md` を Agent に指定します" in ja
    assert "タスクが明示的にネットワーク使用を許可しない限り、ライブフォールバックを無効にします。" in ja
    assert "公開前の準備状況チェックだけ" in ja
    assert "`reference` の欠落、`data` の不正、`verses` または `passages` の不正、節エントリの不正、節本文の欠落" in ja


def test_local_agent_smoke_transcript_is_documented() -> None:
    transcript = _read("docs/local-agent-smoke-transcript.md")
    readme = _read("README.md")
    zh = _read("README-zh.md")
    ja = _read("README-ja.md")

    assert "# Local-first agent smoke-test transcript" in transcript
    assert "Network: disabled after fixture preparation" in transcript
    assert "python scripts/create_tiny_fixture_cache.py /tmp/bible-skill-smoke-data" in transcript
    assert "bible-skill validate --data-dir /tmp/bible-skill-smoke-data" in transcript
    query_command = 'bible-skill query toy "John 3:16" --data-dir /tmp/bible-skill-smoke-data --markdown --attribution'
    assert query_command in transcript
    assert "Fixture loved line." in transcript
    assert "bible-skill skill --data-dir /tmp/bible-skill-smoke-data" in transcript
    assert "Do not use live fallback during this smoke test" in transcript

    for text in (readme, zh, ja):
        assert "docs/local-agent-smoke-transcript.md" in text
        assert "scripts/create_tiny_fixture_cache.py" in text
