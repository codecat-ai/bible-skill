# Roadmap

Bible Skill is in the portfolio **growth** tier, with a target cadence of **1 focused session/week**.

## Completion Review

The previous roadmap item to add richer diagnostics for live provider schema changes is complete. `BibleApiClient.passage()` now validates live payloads before rendering, preserves raw `--json` output for valid supported payloads, and reports non-retryable schema diagnostics for missing `reference`, missing text-bearing fields, malformed `data`, malformed `verses` or `passages`, malformed verse entries, and missing verse text. CLI stderr surfaces those diagnostics without the transient live retry hint, and the generated skill text plus English, Chinese, and Japanese READMEs document the behavior.

The previous roadmap item to improve live provider resilience is complete. Transient HTTP and network provider failures are now covered by offline fixtures, carry retryable classification through `ProviderError`, and show live-only stderr guidance to try `--retries 2` when no retry count was requested. Invalid JSON, unsupported provider schema, and semantic non-retryable HTTP failures do not get retry guidance. The generated skill text and English, Chinese, and Japanese READMEs document the behavior without adding package-registry install claims.

The previous roadmap item to expand offline/local-only agent setup guidance using source-checkout workflows only is complete. The generated skill text and English, Chinese, and Japanese READMEs now show a source checkout, local virtual environment, `uv pip install -e '.[dev]'`, local data directory validation, `bible-skill skill --data-dir ...`, and local-first agent usage without adding package-registry install claims.

The previous roadmap item to prepare packaged release readiness checks without registry install claims is complete. `bible-skill release check` now inspects source-checkout packaging metadata, top-level README/LICENSE files, MIT license text, built artifact metadata when a `dist/` directory is available, and README variants for unverified registry install claims. It provides human-readable output and parseable `--json` output without publishing anything or claiming package-registry availability.

The previous roadmap item to add optional local passage export metadata for translation license and source attribution is complete. Local `query` and `compare` exports now support `--attribution`, and the documentation describes the resulting `license_url` and `source_url` behavior.

The previous roadmap item to review cache portability across operating systems and scripted automation contexts is complete. `Store.cache_manifest()` and `bible-skill cache manifest --json` now expose a deterministic, JSON-serializable cache inspection manifest with POSIX-style relative paths, validation status, issue lists for missing or corrupt caches, and documentation examples for transfer, revalidation, and agent failure handling without packaging or registry claims.

The previous roadmap item to repair and document local cache recovery workflows for invalid cache entries is complete. `Store.prune_invalid_cache_entries()` and `bible-skill cache prune` now validate cache directories, default to dry-run output, remove only invalid translation cache directories with `--yes`, preserve valid entries, report missing requested IDs without deleting unrelated caches, and document the validate, manifest, dry-run prune, confirmed prune, and re-download flow in the generated skill and synchronized READMEs.

The previous roadmap item to tighten cache/import validation is complete. `Store.validate_translation()` now validates the sidecar `metadata.json` alongside `translation.json`, reports missing or malformed sidecar metadata, detects checksum drift, flags metadata mismatches, and lets cache manifests surface those issues without aborting manifest generation.

The first manual source-checkout release-candidate evaluation is complete. On 2026-05-20, a fresh local verification run passed `ruff check .`, `ruff format --check .`, `pytest -q` with 144 tests, `python -m build`, JSON validation for `bible-skill release check --json`, and `bible-skill release check --dist-dir dist` against the generated wheel and sdist. The artifacts matched the `pyproject.toml` name/version metadata, README variants made no unverified registry install claims, and no package-registry release was published or documented.

The maintainer-facing release checklist is complete. `RELEASE_CHECKLIST.md` now keeps the release boundary, source-checkout verification commands, built-artifact review, documentation truthfulness checks, optional smoke checks, and explicit no-registry-publication notes together. It reinforces that registry install instructions must wait for an approved and verified package-registry release.

The project remains growth rather than maintenance because it is useful and tested, but still has active adoption work ahead: release packaging should not be advertised until a maintainer explicitly approves and verifies a real registry release.

## Now

- Add a documented smoke-test transcript for the most common local-first agent workflow using a tiny fixture cache, so maintainers can verify UX changes without network access.

## Next

- Review whether the release checklist and smoke-test transcript are enough to lower cadence from growth to maintenance, or whether one more release-readiness gap remains before cadence reduction.

## Later

- Evaluate additional allowed translation providers only when their licensing and attribution requirements can be represented clearly.
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
