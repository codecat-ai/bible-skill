# Roadmap

Bible Skill is in the portfolio **growth** tier, with a target cadence of **1 focused session/week**.

## Completion Review

The previous roadmap item to add optional local passage export metadata for translation license and source attribution is complete. Local `query` and `compare` exports now support `--attribution`, and the documentation describes the resulting `license_url` and `source_url` behavior.

The project remains growth rather than maintenance because it is useful and tested, but still has active adoption work ahead: provider resilience needs more hardening, offline/local-only agent setup should be easier to follow, cache import and validation paths can be stricter, and release packaging should not be advertised until it has been manually verified.

## Now

- Improve live provider resilience with clearer retry guidance, failure fixtures, and documented behavior for transient HTTP and network errors.
- Expand offline/local-only agent setup guidance using source-checkout workflows only.
- Tighten cache/import validation so agents can detect missing metadata, malformed content, and checksum drift before relying on local passages.

## Next

- Add practical examples for local-only skill export and validation flows in agent environments.
- Review cache portability across operating systems and scripted automation contexts.
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
- Reclassify to maintenance only after offline setup guidance, cache validation, provider resilience, and release readiness are stable enough that most sessions are reactive rather than roadmap-driven.

## Completion Review Rules

- Remove completed work from future roadmap bullets in the same change that documents completion.
- Keep README roadmap summaries synchronized across English, Chinese, and Japanese.
- Do not claim package registry installation paths until they have been manually verified.
- Keep production code changes out of roadmap-only reviews.
- Before closing a roadmap review, run the documented checks and confirm stale future wording is absent.
