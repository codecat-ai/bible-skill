# Roadmap

Bible Skill is in the portfolio **growth** tier, with a target cadence of **1 focused session/week**.

## Completion Review

The previous roadmap item to expand offline/local-only agent setup guidance using source-checkout workflows only is complete. The generated skill text and English, Chinese, and Japanese READMEs now show a source checkout, local virtual environment, `uv pip install -e '.[dev]'`, local data directory validation, `bible-skill skill --data-dir ...`, and local-first agent usage without adding package-registry install claims.

The previous roadmap item to add optional local passage export metadata for translation license and source attribution is complete. Local `query` and `compare` exports now support `--attribution`, and the documentation describes the resulting `license_url` and `source_url` behavior.

The previous roadmap item to review cache portability across operating systems and scripted automation contexts is complete. `Store.cache_manifest()` and `bible-skill cache manifest --json` now expose a deterministic, JSON-serializable cache inspection manifest with POSIX-style relative paths, validation status, issue lists for missing or corrupt caches, and documentation examples for transfer, revalidation, and agent failure handling without packaging or registry claims.

The previous roadmap item to tighten cache/import validation is complete. `Store.validate_translation()` now validates the sidecar `metadata.json` alongside `translation.json`, reports missing or malformed sidecar metadata, detects checksum drift, flags metadata mismatches, and lets cache manifests surface those issues without aborting manifest generation.

The project remains growth rather than maintenance because it is useful and tested, but still has active adoption work ahead: provider resilience needs more hardening, cache repair workflows can improve, and release packaging should not be advertised until it has been manually verified.

## Now

- Improve live provider resilience with clearer retry guidance, failure fixtures, and documented behavior for transient HTTP and network errors.

## Next

- Prepare packaged release readiness checks without publishing or documenting registry install commands before verification.

## Later

- Evaluate additional allowed translation providers only when their licensing and attribution requirements can be represented clearly.
- Consider richer diagnostics for provider schema changes and local cache repair workflows.
- Publish package installation guidance only after a real release path is manually verified.

## Maintenance Triggers

- Upstream provider response shapes, rate limits, or availability change.
- Validation misses corrupted or incomplete local cache files.
- Generated `skills/bible-skill/SKILL.md` drifts from supported CLI behavior.
- Packaging metadata changes, or a registry release is created and manually verified.
- Translation metadata or attribution requirements change.

## Cadence Review Notes

- Plan one focused session per week while the project is in growth.
- Use each session to close one narrow documentation, validation, provider, or release-readiness gap.
- Reclassify to maintenance only after cache validation, cache portability, provider resilience, and release readiness are stable enough that most sessions are reactive rather than roadmap-driven.

## Completion Review Rules

- Remove completed work from future roadmap bullets in the same change that documents completion.
- Keep README roadmap summaries synchronized across English, Chinese, and Japanese.
- Do not claim package registry installation paths until they have been manually verified.
- Keep production code changes out of roadmap-only reviews.
- Before closing a roadmap review, run the documented checks and confirm stale future wording is absent.
