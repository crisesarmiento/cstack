# Changelog

All notable changes to cstack are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0-pilot.1] - 2026-11-21

Pre-release for the first pilot run. It is not the full v0.1.0 described in
[#1](https://github.com/crisesarmiento/cstack/issues/1): principles, cost rules,
presets and the installer are still missing.

### Added

- `correct` skill: find recurring repository mistakes and prevent them
  structurally ([#6](https://github.com/crisesarmiento/cstack/pull/6)).
- `sharpen` skill: make a task prompt deeper, not longer
  ([#6](https://github.com/crisesarmiento/cstack/pull/6)).
- `verify-template` skill: generate a project's own `verify-<app>` skill, with
  an illustrative feature map example
  ([#6](https://github.com/crisesarmiento/cstack/pull/6)).
- CI check that fails if any file under `skills/` names a model or model vendor
  ([#6](https://github.com/crisesarmiento/cstack/pull/6)).
- MIT license and attribution to pstack 0.15.46
  ([#5](https://github.com/crisesarmiento/cstack/pull/5)).
- Specs 0001 (structure and versioning) and 0002 (first skills).

[Unreleased]: https://github.com/crisesarmiento/cstack/compare/v0.1.0-pilot.1...HEAD
[0.1.0-pilot.1]: https://github.com/crisesarmiento/cstack/releases/tag/v0.1.0-pilot.1
