# Bible Skill

Use installed local translation data first for exact Scripture lookup. Do not quote from memory when a local query can answer the request.

## Commands

- List installed translations: `bible-skill installed --data-dir ./data`
- Search installed translation metadata: `bible-skill search QUERY --data-dir ./data`
- Query exact local passages: `bible-skill query TRANSLATION_ID REFERENCE --data-dir ./data`
- Compare an exact passage across local translations: `bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir ./data`
- Export a comparison as Markdown for notes or agent context: `bible-skill compare REFERENCE TRANSLATION_ID OTHER_TRANSLATION_ID --data-dir ./data --markdown`
- List downloadable translations: `bible-skill translations`
- Download an allowed translation: `bible-skill download TRANSLATION_ID --data-dir ./data`
- Use live fallback only when local data is unavailable: `bible-skill live "John 3:16" --translation web`

## Operating Rules

Prefer local installed data, cite the returned normalized reference and translation id, and preserve exact wording from the tool output. Respect translation metadata and license URLs.
