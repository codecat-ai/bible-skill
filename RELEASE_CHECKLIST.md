# Release Checklist

Bible Skill is currently a **source-checkout-only** project. This checklist helps maintainers evaluate release readiness without publishing, documenting, or implying any package-registry availability.

Use this checklist before proposing a manual release, after packaging metadata changes, or whenever `bible-skill release check` reports new readiness issues.

## Release boundary

- [ ] Confirm the release is a manual maintainer decision, not an autonomous package-registry publication.
- [ ] Confirm no registry install command has been added to `README.md`, `README-zh.md`, `README-ja.md`, generated skill text, examples, issue templates, or release notes unless that registry artifact has already been published and verified.
- [ ] Keep the user-facing install path source-checkout-only until a real registry release is approved.
- [ ] Confirm Bible text is not bundled into the repository, wheel, sdist, docs, examples, or generated skill artifacts.
- [ ] Confirm translation licensing and attribution wording still tells users to respect translation terms.

## Source checkout verification

Run these checks from a clean checkout on the intended commit:

```sh
git status --short
ruff check .
ruff format --check .
pytest -q
bible-skill release check --json
python -m build
bible-skill release check --dist-dir dist
```

Expected result:

- [ ] The worktree is clean before release verification starts.
- [ ] Lint, format, and tests pass.
- [ ] `bible-skill release check --json` emits parseable JSON and reports no failing checks.
- [ ] `python -m build` creates a wheel and sdist under `dist/`.
- [ ] `bible-skill release check --dist-dir dist` reports built artifact metadata that matches `pyproject.toml`.

## Built artifact review

Inspect the generated artifacts before any release decision:

- [ ] Wheel name and version match `pyproject.toml`.
- [ ] Sdist name and version match `pyproject.toml`.
- [ ] Top-level `LICENSE` is present and contains MIT license text.
- [ ] English, Chinese, and Japanese README files are included or otherwise accounted for by the packaging metadata.
- [ ] No generated artifact includes local cache data, downloaded Bible text, virtual environments, `dist/` from a previous run, or test caches.
- [ ] Generated `skills/bible-skill/SKILL.md`, if refreshed, matches the source renderer output.

## Documentation truthfulness

Review the docs and generated skill text together:

- [ ] `README.md`, `README-zh.md`, and `README-ja.md` all include the language switcher.
- [ ] All README variants state that the package is not published to a package registry yet.
- [ ] Installation and quick-start sections use clone/source-checkout commands only.
- [ ] Development instructions mention `bible-skill release check`, build verification, and this checklist.
- [ ] Roadmap wording distinguishes completed readiness work from future release approval.
- [ ] Generated skill text does not claim `pip install`, `uvx`, Homebrew, Docker, or any other registry/image installation path.

## Optional smoke checks

When the release touches CLI behavior, run representative smoke checks against a tiny local fixture cache or existing test fixture data:

```sh
bible-skill --help
bible-skill release check
bible-skill release check --json
```

If network use is explicitly allowed for the review, a maintainer may also run a bounded live fallback query, but live provider availability must not be required for release readiness.

## Approval and publication notes

- [ ] If a maintainer approves an actual package-registry release later, verify the published artifact with the registry's read-only lookup command before adding registry install instructions.
- [ ] Record the exact verification commands, artifact names, and registry lookup result in release notes.
- [ ] Do not publish package-registry releases from autonomous maintenance runs.
