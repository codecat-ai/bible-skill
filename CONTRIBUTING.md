# Contributing

Thank you for helping improve Bible Skill. This project is developed from a clean-room brief and must not copy code or prose from external Bible lookup projects.

## Development Expectations

- Use Python 3.11 or newer.
- Keep runtime dependencies in the Python standard library unless a maintainer approves otherwise.
- Use `urllib` for HTTP clients.
- Write behavior-focused tests before implementation changes.
- Do not add Bible text to the repository except tiny artificial test fixtures.
- Use English code comments and commit messages.
- Use Conventional Commit messages, such as `feat: add local passage query`.
- Do not add `Co-authored-by` trailers.

## Checks

Run these checks before opening a pull request from a prepared development environment:

```sh
ruff check .
ruff format --check .
pytest -q
python -m build
```

## Documentation

Keep `README.md`, `README-zh.md`, and `README-ja.md` synchronized in meaning. Each README must begin with:

```md
[English](README.md) | [中文](README-zh.md) | [日本語](README-ja.md)
```

Document source-checkout-only usage until a maintainer verifies and approves a package-registry release.
