from __future__ import annotations


def tiny_translation() -> dict:
    return {
        "metadata": {
            "id": "toy",
            "name": "Toy Test Translation",
            "language": "en",
            "license": "Test fixture only",
            "license_url": "https://example.invalid/license",
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
            {
                "id": "1JN",
                "name": "1 John",
                "chapters": [
                    {
                        "number": 1,
                        "verses": [
                            {"number": 1, "text": "Fixture first letter line."},
                        ],
                    }
                ],
            },
        ],
    }
