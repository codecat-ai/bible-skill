#!/usr/bin/env python3
"""Create a tiny offline Bible Skill cache for smoke tests."""

from __future__ import annotations

import argparse
from pathlib import Path

from bible_skill.store import Store


def tiny_translation() -> dict:
    """Return deterministic fixture data for local smoke-test workflows."""
    return {
        "metadata": {
            "id": "toy",
            "name": "Toy Test Translation",
            "language": "en",
            "license": "Test fixture only",
            "license_url": "https://example.invalid/license",
            "source_url": "https://example.invalid/toy-translation.json",
        },
        "books": [
            {
                "id": "GEN",
                "name": "Genesis",
                "chapters": [
                    {
                        "number": 1,
                        "verses": [
                            {"number": 1, "text": "Fixture beginning line."},
                            {"number": 2, "text": "Fixture second line."},
                        ],
                    }
                ],
            },
            {
                "id": "JHN",
                "name": "John",
                "chapters": [
                    {
                        "number": 3,
                        "verses": [
                            {"number": 16, "text": "Fixture loved line."},
                            {"number": 17, "text": "Fixture sent line."},
                            {"number": 18, "text": "Fixture believed line."},
                        ],
                    },
                    {
                        "number": 4,
                        "verses": [
                            {"number": 1, "text": "Fixture travel line."},
                            {"number": 2, "text": "Fixture witness line."},
                        ],
                    },
                ],
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a tiny local Bible Skill fixture cache.")
    parser.add_argument("data_dir", type=Path, help="Directory where the fixture cache should be written.")
    args = parser.parse_args()

    Store(args.data_dir).save_translation("toy", tiny_translation())
    print(f"Wrote toy fixture cache to {args.data_dir / 'translations' / 'toy'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
