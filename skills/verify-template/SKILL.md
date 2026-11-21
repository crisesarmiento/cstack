---
name: verify-template
description: Generate a project-owned verify-<app> skill that launches, diagnoses, drives, and captures evidence from the real app. Use only when the user asks for a behavioral proof workflow or a project lacks one; run once per project, then only to regenerate.
metadata:
  source: pstack 0.15.46
  upstream-skill: create-verification-skill
  author: Lauren Tan
  license: MIT
  attribution: Adapted from pstack; see NOTICE.md in cstack.
---

# Generate a verification skill

Run this generator from a cstack checkout or through `npx skills`, targeting
the consumer repository. Do not copy or commit `verify-template` into that
project. If npx skills installed it into the project, remove it after generation; never commit it.
Commit only its generated `verify-<app>` and relative symlink.
Honor the project's approval gates before writing or running anything.

## Discover and establish a baseline

Interview the repository, not the user: inspect its README, development commands,
scripts, tests, and entry points. Determine the user surface, how to run and
drive it, what proves a result, and how to isolate state. Ask only what the
repository cannot answer. Do not add dependencies or services without approval.

Build and launch the checkout using its documented commands. Fix a broken
baseline within approved scope, or report the exact command, exit status,
failure, and blocker before generating; never invent a working recipe.

Prefer existing repository tests and scripts. Use only tools callable through
plain shell from the repository root: for example an existing browser test
runner, a terminal/PTY session, or `curl`. Never require an agent's built-in
browser or named tool. For games, use the repository's existing headless or CI
entry point; report absent coverage rather than inventing one.

## Generate the project-owned files

Derive a lowercase, hyphenated `verify-<app>` identifier, at most 64 characters.
Create:

```text
.agents/skills/verify-<app>/SKILL.md
.agents/skills/verify-<app>/features/README.md
.agents/skills/verify-<app>/features/<feature>.md
.agents/skills/verify-<app>/scripts/       # only if needed
.claude/skills/verify-<app> -> ../../.agents/skills/verify-<app>
```

Replace every placeholder with a real project value. Use standard frontmatter:
`name` matching the directory and a non-empty `description` of at most 1024
characters explaining purpose and trigger. Keep instructions short and
imperative. Use no model names, routing defaults, or harness-specific tools.
Write no other vendor directories.

Never overwrite an existing generated skill, its files, or an occupied symlink
path. Propose a diff instead and await approval; do not apply it implicitly.
Create the relative symlink only when its path is free.

Give the generated `SKILL.md` these six sections:

### Launch

Specify exact repository-relative commands, working directory, prerequisites,
isolated state, and how to track processes started by this run. Define readiness
as usable application behavior, not merely a live process or responding port.
Include migrations and seed data needed from an empty data directory, a bounded
wait, and actionable failure output. Refuse to drive shared state when isolation
is unavailable.

### Doctor

Provide read-only checks for prerequisites, readiness, and baseline state.
Check instance ownership and build identity before driving and whenever anything
looks wrong.
Diagnose failures without resetting data, installing software, or changing
configuration. Name environment variables and test-account references only;
never read, print, or store their secret values.

### Drive

Link the feature index. Give commands and real selectors, routes, arguments, or
inputs discovered in the repository. Exercise a real user journey and assert
the resulting state and side effects, not just a successful exit or click.
Never weaken the journey to make it pass. Allow mocks only at existing
production boundaries; state exactly what any dry run skips.
Observe files, network, and other relevant side effects to establish those
skips rather than trusting the mode's name.

### Evidence

Specify a persistent repository-relative evidence directory outside disposable
runtime state, with run-specific filenames. Capture the action, resulting
state, and relevant side effects using logs, screenshots, assertions, or
artifacts appropriate to the surface. Exclude secrets and sensitive data.
Record commands, exit statuses, and artifact paths. Document what a stand-in
environment did that the real target will not, and all untested boundaries.
Make reviewers inspect evidence before the diff.

### Cleanup

Stop only processes started by this run, using tracked identities rather than
broad kill commands. Remove only owned temporary state; preserve pre-existing
user data and all named evidence. Provide cleanup for failure paths too.

### Helpers

List each necessary helper's purpose and exact shell invocation, or state
that none are needed. Make generated scripts executable. Prefer existing
scripts; do not add tooling merely to wrap an existing command.

## Map the features

Write `features/README.md` with an index of the top 3–5 user-facing features,
shared baseline preconditions, isolation requirements, and proof standards.
Require a real user path, action plus resulting state, and side-effect checks.
Explain permitted boundary mocks and dry-run limitations.

Create at least three feature files. Follow the shape of
[feature-map example](references/feature-map-example/index.md) — its commands are illustrative, invented
for a fictional app and never executed — and replace them with real commands,
selectors, and paths discovered in the repository. Give each file exactly
these four H2s, replacing `<harness>` with the actual shell-callable driving
mechanism:

- `Sub-features`: observable behaviors and expected outcomes.
- `How to get to it (user POV)`: the user's route from the baseline.
- `Driving it with <harness>`: exact commands, inputs, assertions, and evidence.
- `Gotchas`: prerequisites, timing, isolation, cleanup, and environment limits.

## Prove and hand over

Follow the generated skill once, end to end: launch → doctor → drive one mapped
feature → evidence → cleanup. Confirm the named evidence still exists after
cleanup. Report commands, exit statuses, observed outcomes, artifact paths,
and limitations; do not claim success for a blocked or simulated run.

Have a second agent independently repeat that same journey from the generated
skill alone, if your agent supports subagents. Otherwise request an independent
agent run and report it pending; a serial self-check is not independent proof.

Stop at proposed changes or an authorized local commit. Never merge, push to a
default branch, or deploy. For later drift, update the project-owned skill
through review, or rerun this generator to propose a diff; no maintenance
skill is shipped in this version.
