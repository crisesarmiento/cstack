# Changelog

All notable changes to cstack are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Agent-agnostic shell permission rules: exact-command allows without wildcards,
  interactive verification, dated OpenCode evidence and explicit consumer
  responsibilities; no automated permission enforcement yet
  ([#10](https://github.com/crisesarmiento/cstack/issues/10)).
- Agent-agnostic rule that only the orchestrator runs verification; delegated
  specialists change code and report back, with Londinium pilot evidence and
  no automated enforcement
  ([#12](https://github.com/crisesarmiento/cstack/issues/12)).

## [0.1.0] - 2026-11-21

### Added

- One checklist containing the eight implementation principles adapted from
  pstack 0.15.46, with applicability and concrete failure signals.
- Cost and model policy with preset, CI and bot enforcement responsibilities.
- An oh-my-opencode-slim 3.0.7 preset template with role intent, additive skill
  grants and project-filled model placeholders.
- A short project context template and relative `CLAUDE.md -> AGENTS.md` guidance.
- A pinned POSIX installer, relative Claude skill links and a version/tag/commit
  lock file, with dependency-free CI coverage.

### Changed

- Promoted `VERSION` and `cstack.json` from the pilot to `0.1.0`.
- Documented both pinned install paths, consumer adoption and the remaining
  pilot validation gaps from [#8](https://github.com/crisesarmiento/cstack/issues/8).

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

[Unreleased]: https://github.com/crisesarmiento/cstack/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/crisesarmiento/cstack/compare/v0.1.0-pilot.1...v0.1.0
[0.1.0-pilot.1]: https://github.com/crisesarmiento/cstack/releases/tag/v0.1.0-pilot.1
