from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_english_readme_documents_source_checkout_offline_agent_setup() -> None:
    text = _read("README.md")

    assert "## Offline/local-only agent setup" in text
    assert "python -m venv .venv" in text
    assert "uv pip install -e '.[dev]'" in text
    assert "bible-skill validate --data-dir ./data" in text
    assert "bible-skill cache manifest --data-dir ./data --json" in text
    assert "bible-skill skill --data-dir ./data > skills/bible-skill/SKILL.md" in text
    assert "Point the agent at the generated `skills/bible-skill/SKILL.md`" in text
    assert "Disable live fallback unless a task explicitly permits network use." in text
    assert "Do not use `pip install bible-skill`, `uvx bible-skill`, or similar registry commands" in text


def test_translated_readmes_document_matching_offline_agent_setup() -> None:
    zh = _read("README-zh.md")
    ja = _read("README-ja.md")

    for text in (zh, ja):
        assert "python -m venv .venv" in text
        assert "uv pip install -e '.[dev]'" in text
        assert "bible-skill validate --data-dir ./data" in text
        assert "bible-skill cache manifest --data-dir ./data --json" in text
        assert "bible-skill skill --data-dir ./data > skills/bible-skill/SKILL.md" in text
        assert "pip install bible-skill" in text
        assert "uvx bible-skill" in text

    assert "## 离线/仅本地 Agent 设置" in zh
    assert "将 Agent 指向生成的 `skills/bible-skill/SKILL.md`" in zh
    assert "除非任务明确允许网络使用，否则禁用实时后备。" in zh

    assert "## オフライン/ローカル専用 Agent セットアップ" in ja
    assert "生成した `skills/bible-skill/SKILL.md` を Agent に指定します" in ja
    assert "タスクが明示的にネットワーク使用を許可しない限り、ライブフォールバックを無効にします。" in ja
