# Project context

Replace the placeholders with commands and paths verified in this repository.

## Build and test

- Build: `<build command from the repository root>`
- Test: `<test command from the repository root>`
- Focused verification: `<command for the changed feature>`
- Architecture and domain vocabulary: `<relative path to architecture docs>`

## Review

Look at evidence before the diff: show the command, exit status and observable
result for the changed behavior. Name checks you could not run and why.

## Shared guidance

- Rule placement and enforcement: [rules/](rules/).
- Cost, routing and Decisions: [rules/cost-and-models.md](rules/cost-and-models.md).
- Shell permissions: [rules/agent-permissions.md](rules/agent-permissions.md).
  Allow only exact commands without wildcards; variable arguments stay on ask.
  Never pre-allow push, PR operations, merge, sudo or secret reads.
  Verify prompts interactively; cstack does not enforce these permissions.
- Only the orchestrator runs tests, builds and verify scripts; delegated agents
  change code and report back. See [rules/agent-permissions.md](rules/agent-permissions.md#3-only-the-orchestrator-runs-verification).
- Open pull requests ready for review, never as drafts (e.g. no `gh pr create --draft`);
  reviews
  run once, when the PR opens.
- Design and implementation checklist: [principles/PRINCIPLES.md](principles/PRINCIPLES.md).
- Project-specific verification skill: `.agents/skills/verify-<app>/SKILL.md`.

Checkable rules do not belong here: put them in types, lint, tests or CI.
Keep this file for context; use short skills for judgment.

`AGENTS.md` is canonical. At the repository root, create and commit the relative
symlink `CLAUDE.md -> AGENTS.md` (`ln -s AGENTS.md CLAUDE.md`) after checking that
`CLAUDE.md` does not already contain project guidance that needs to be merged.
