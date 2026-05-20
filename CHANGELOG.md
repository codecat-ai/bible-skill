# Changelog

## Unreleased

- Add `bible-skill release check` for source-checkout-only packaging and documentation readiness checks with human and JSON output, including artifact metadata inspection when `dist/` is available.
- Tighten local cache validation to inspect sidecar `metadata.json`, report missing or malformed sidecars, detect checksum drift, and surface sidecar issues through cache manifests.
- Add offline/local-only source-checkout setup guidance to the generated skill and synchronized READMEs.
- Add local installed-translation metadata search with text and JSON CLI output.
- Initial clean-room implementation with local passage parsing, storage, providers, CLI, tests, and documentation.
