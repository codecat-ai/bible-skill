# Bible Skill

Use installed local translation data first for exact Scripture lookup. Do not quote from memory when a local query can answer the request.

## Commands

- List installed translations: `bible-skill installed --data-dir ./data`
- Query exact local passages: `bible-skill query TRANSLATION_ID REFERENCE --data-dir ./data`
- List downloadable translations: `bible-skill translations`
- Download an allowed translation: `bible-skill download TRANSLATION_ID --data-dir ./data`
- Use live fallback only when local data is unavailable: `bible-skill live "John 3:16" --translation web`

## Operating Rules

Prefer local installed data, cite the returned normalized reference and translation id, and preserve exact wording from the tool output. Respect translation metadata and license URLs.
