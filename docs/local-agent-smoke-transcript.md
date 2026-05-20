# Local-first agent smoke-test transcript

This transcript documents the smallest repeatable offline workflow for maintainers who want to check Bible Skill UX changes without touching the network. It uses a toy fixture cache, not a real Bible translation, so it is safe for CI-style smoke checks and should not be used for devotional or publication work.

- Project checkout: trusted local source checkout
- Network: disabled after fixture preparation
- Data directory: `/tmp/bible-skill-smoke-data`
- Fixture translation ID: `toy`

## 1. Prepare the tiny fixture cache

```console
$ python scripts/create_tiny_fixture_cache.py /tmp/bible-skill-smoke-data
Wrote toy fixture cache to /tmp/bible-skill-smoke-data/translations/toy
```

## 2. Validate the local cache before agent use

```console
$ bible-skill validate --data-dir /tmp/bible-skill-smoke-data
toy	ok	sha256:774965d12bd346fc0a1d1790453696175b50acbb72f983b74e6af1193e7cff68
```

## 3. Inspect the cache manifest for automation

```console
$ bible-skill cache manifest --data-dir /tmp/bible-skill-smoke-data --json
{
  "translations": [
    {
      "id": "toy",
      "name": "Toy Test Translation",
      "language": "en",
      "relative_path": "translations/toy/translation.json",
      "validation_ok": true,
      "issues": []
    }
  ],
  "issues": []
}
```

The real JSON also includes stable counts, source metadata, timestamps, and checksums. Automation should fail if either the top-level `issues` list or a translation-level `issues` list is non-empty.

## 4. Generate the agent skill text against the same data directory

```console
$ bible-skill skill --data-dir /tmp/bible-skill-smoke-data
# Bible Skill

Use installed local translation data first for exact Scripture lookup. Do not quote from memory when a local query can answer the request.
```

Point the agent at this generated skill text and keep the same `--data-dir` in every lookup command. Do not use live fallback during this smoke test; the point is to prove local cache behavior is deterministic and network-free.

## 5. Query the fixture passage as Markdown with attribution

```console
$ bible-skill query toy "John 3:16" --data-dir /tmp/bible-skill-smoke-data --markdown --attribution
# John 3:16 (toy)

> License: https://example.invalid/license
> Source: https://example.invalid/toy-translation.json

- **John 3:16** Fixture loved line.
```

Expected maintainer checks:

1. The command succeeds without network access.
2. The output preserves the exact fixture wording `Fixture loved line.`.
3. Attribution is present when `--attribution` is requested.
4. No registry install command such as `pip install bible-skill` or `uvx bible-skill` is required or implied.

## 6. Clean up

Only remove the temporary smoke-test directory you created for this run. Never point cleanup commands at a real shared Bible Skill cache.
