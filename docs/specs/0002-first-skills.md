# Spec: cstack's first three skills

- **Date:** 21/11/2026 (America/Cordoba)
- **Issue:** [#1](https://github.com/crisesarmiento/cstack/issues/1) (v0.1 scope: `correct`, `verify-template`, `sharpen`)
- **Depends on:** [0001-structure-and-versioning.md](0001-structure-and-versioning.md) (source in `skills/<id>/SKILL.md`; consumers get `.agents/skills/<id>/` plus a relative symlink `.claude/skills/<id>`; `AGENTS.md` is canonical)
- **Status:** proposal, not implemented. No `SKILL.md` is written by this PR.

Sources consulted on 21/11/2026: pstack 0.15.46 (local copy of the plugin, MIT) skills `correct`, `sharpen`, `create-verification-skill` (with `references/feature-map-example/`) and `maintain-verification-skill`; the pstack review of 21/11/2026 (Vault `Research/AI-Dev-Tooling/2026-11-21-pstack-revision.md`); the [Agent Skills specification](https://agentskills.io/specification).

## 1. Shared requirements (all three skills)

These apply to every skill below and are not repeated per skill.

**Format.** Agent Skills standard: a folder `skills/<id>/` with `SKILL.md`, YAML frontmatter with `name` and `description`, Markdown body. `name` matches the folder name (lowercase, digits, hyphens; max 64 characters). `description` is at most 1024 characters and says what the skill does **and** when to use it, because some agents pick skills from the description alone. Optional standard folders only: `scripts/`, `references/`, `assets/`.

**Agent-agnostic.** Each skill must work, unchanged, in OpenCode, Claude Code, Cursor, Codex and pi (read from `.agents/skills/`, or from `.claude/skills/` through the symlink for Claude Code). Concretely:

- No model names, model tiers, reasoning budgets or "use a stronger model" steps. No defaults that select a paid model. Model choice belongs to the user's harness config (for Cristian's setup, the slim preset), never to the skill.
- No dependency on one harness's tools: no named subagent/Task tool, built-in browser, plugin, rule file or slash command. If a step benefits from parallel subagents, the skill says "if your agent supports subagents"; the serial path must also work.
- Commands are plain shell that any agent can run from the repo root. Paths are repo-relative.
- No vendor folders in outputs: generated files go to `.agents/skills/` (plus the Claude symlink), never `.cursor/`, `.opencode/`, `.codex/` or `.pi/`.
- The invocation name (`/correct`, `$correct`, a skill picker) differs per agent, so the body never assumes one.

**Size.** Short enough to read cold mid-task. Proposed targets: `sharpen` ≤ 200 words, `correct` ≤ 450, `verify-template` ≤ 1100 for `SKILL.md` (examples go in `references/`).

**Safety.** A skill never prints or stores secret values (tokens, `.env` contents, keys). It may name an environment variable, not its value. No skill merges, pushes to a default branch or deploys; it stops at a local commit or a proposed change.

**Shared acceptance criteria.**

1. Frontmatter passes a check: `name` equals the folder name, `description` is non-empty and ≤ 1024 characters.
2. A grep-based check in cstack CI fails if any file under `skills/` names a model or model vendor (the pattern list lives in the check, not in prose). This encodes the "no model names" rule in structure.
3. In a real Orca worktree of the pilot repo, the skill is listed and can be invoked in OpenCode, Claude Code, Cursor, Codex and pi. The result per agent (loaded / not loaded, version used) is recorded in the implementation PR.

## 2. `correct`

**Purpose.** Find mistakes that agents repeat in a repo and make each one impossible, by fixing it at the highest structural level that works. This is cstack's main rule-placement tool (issue #1: checkable → lint/types/tests/CI; judgement → a short skill; context → `AGENTS.md`).

**When it triggers.** When the same mistake class has happened at least twice, or when the user corrects an agent for something a rule already covers. Invoked by the user, not automatically on every task (see open question 2).

**Inputs.** The repo itself: recent commits, reverts, review comments, `AGENTS.md`, and comments that explain workarounds. Optionally, the correction the user just made.

**Outputs.**

- A list of mistake classes, each with evidence (commits, review comments), the chosen level, and why a higher level did not work. This is the reply format, kept from upstream.
- For each fixed class: one commit with the fix and a check that **fails on a real past mistake** (shown in the commit or PR).
- An updated rule table: each rule paired with what enforces it.

**Adapted from pstack.** Kept as is: the "assume every contributor is an agent that sees only the files it opened" framing; the order architecture → types → lint/CI whose error names the fix → behavior test → docs last; "a class counts once it has happened twice"; prove each check fails on a past mistake; run the same command locally and in CI; exceptions on the offending line with a reason, an expiry date and a human's approval; fail only on new occurrences when a pattern is already common; drop a rule once its mistake can't happen.

**Dropped or changed.**

- "Agent instruction file" becomes `AGENTS.md` explicitly (canonical in cstack consumers). Where the rule table lives is open (question 3), because spec 0001 keeps `AGENTS.md` short.
- The description no longer says "Use for /correct" (invocation differs per agent).
- Added: stop at local commits. Opening the PR and merging stay with the human, one PR at a time.
- Added: when the fix needs a new dependency or CI job, propose it instead of adding it.

**Acceptance criteria.**

1. Run on the pilot repo, it reports at least one class with two or more pieces of evidence, or says honestly that none qualify.
2. Every check it adds is shown failing on a past mistake (command + output) and passing on the fixed code.
3. No class is fixed only with docs when a higher level was possible without the reply explaining why.

**Open questions.** Rule table location (question 3). Whether `correct` may add a CI job or only propose one.

## 3. `verify-template`

**Purpose.** Generate a project-local skill, `verify-<app>`, that drives the real app the way a user does (launch it, exercise a feature, capture evidence), so reviewers look at evidence first and the diff second. cstack ships the generator; each project owns its generated skill.

**When it triggers.** When a project has no scripted way to prove UI, CLI, service or game behavior, or when the user asks for one. Run once per project, then rerun only to regenerate.

**Inputs.** The codebase (dev commands, scripts, README, existing test harnesses). The user is asked only what the repo cannot answer.

**Outputs** (in the consumer repo):

```
.agents/skills/verify-<app>/
  SKILL.md                # name: verify-<app>; Launch, Doctor, Drive, Evidence, Cleanup, Helpers
  features/README.md      # index + baseline preconditions + proof standards
  features/<feature>.md   # top 3-5 user-facing features
  scripts/                # only if needed; executable, invocation shown in SKILL.md
.claude/skills/verify-<app> -> ../../.agents/skills/verify-<app>
```

Plus a report of the one end-to-end proof run (see acceptance criteria).

**Adapted from pstack** (`create-verification-skill`). Kept: interview the repo, not the user (surface, run, drive, observe, isolate); fix or precisely report a checkout that doesn't build before generating; the six sections and their rules (ready means usable, not just a process answering; a read-only doctor; real selectors and commands from the repo; the proof standards: real user path, action and resulting state, side effects, mocks only at existing production boundaries, observe what a dry-run really skips; kill only what you started; evidence survives cleanup); the feature map with the four H2s `Sub-features`, `How to get to it (user POV)`, `Driving it with <harness>`, `Gotchas`; never weaken a journey to make it pass; prove the generated skill once end to end before handing it over; list what a stand-in environment did that the real target won't. The `references/feature-map-example/` shape is adapted with attribution.

**Dropped or changed.**

- Output path is `.agents/skills/verify-<app>/` plus the Claude symlink, not a vendor folder (spec 0001).
- Harness recipes use tools callable from any agent's shell (the repo's own tests or scripts first, then generic options such as an end-to-end browser test runner, a tmux/PTY session, or `curl`). Never an agent's built-in browser.
- For a game repo (Londinium, Godot), "drive" means whatever headless or CI entry point the repo already has. What Londinium runs today was not verified for this spec.
- Never overwrite an existing `verify-<app>`; propose a diff instead (consistent with `cstack-install` in spec 0001).
- The generated skill names env vars and test accounts by reference only, never their values.
- `maintain-verification-skill` is **not** in v0.1. Its parallel per-feature subagent wave assumes subagents; it can be ported later with a serial path, once a `verify-<app>` exists and has drifted. The generator's last step says so instead of pointing at a skill that isn't shipped.
- The formal-verification variants are out of scope (section 6).

**Acceptance criteria.**

1. On the pilot repo, the generated `verify-<app>` has valid frontmatter, no placeholders, and at least 3 feature files.
2. Its own instructions were run once: launch → doctor → drive one mapped feature → evidence → cleanup, and the evidence still exists at the named location after cleanup.
3. A second agent (different from the one that generated it) can run the same journey from the skill alone.

**Open questions.** How the generator reaches the consumer (question 1). Pilot repo for the first `verify-<app>`. Whether the ID should describe a generator (the upstream name is `create-verification-skill`); issue #1 fixed `verify-template`, so it stays unless changed there.

## 4. `sharpen`

**Purpose.** Make a task deeper, not bigger, then rewrite the prompt. Used before handing a ticket to an agent (for Cristian: before sending work to an OpenCode/Orca session).

**When it triggers.** At the start of a task, on the user's request, when a prompt is vague or asks for less than a professional in that field would do.

**Inputs.** The user's prompt or issue text, and the repo if the task is about code.

**Outputs.** Four short answers (what a top professional would do that wasn't asked; the rawest material they'd start from; their specific methods and tools; what, besides the agent or the user, would show the result is right), then the rewritten prompt, ready to paste into an issue or a session.

**Adapted from pstack.** The four questions and "rewrite my prompt to ask for exactly that" are kept nearly verbatim. Also kept: the rewritten prompt asks the agent to prototype any choice an experiment can settle and recommend an option from what it observed, and leaves product or preference choices to the user.

**Dropped or changed.**

- The description no longer says "Use for /sharpen".
- Added (from pstack's `in-your-own-words`, per the review's suggestion): first restate the goal and the smallest change in one or two lines, so a misunderstanding shows before the rewrite.
- Prototypes are throwaway experiments. The rewritten prompt must not ask for implementation that needs an approved decision first; it ends with the decision to bring back to the user.
- The rewritten prompt names no model, provider or harness role unless the user's prompt did.

**Acceptance criteria.**

1. On three real past issues from the pilot repo, the output has the restatement, the four answers and a rewritten prompt that is deeper (new evidence sources, methods or a check), not just longer.
2. Each rewritten prompt contains a "how we'll know it's right" check that doesn't rely on the agent's own judgement.
3. Product or preference choices are listed for the user, not decided.

**Open questions.** Whether the restatement step stays in `sharpen` or becomes its own skill later.

## 5. Attribution

`correct`, `verify-template` and `sharpen` are adapted from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan, published in [cursor/plugins](https://github.com/cursor/plugins) under the MIT License (Copyright (c) 2026 Lauren Tan). Version used: 0.15.46. Each adapted `SKILL.md` will say so in `metadata` (for example `source: pstack 0.15.46`), and the pstack copyright and license notice will ship with cstack (a `NOTICE` or a section in `LICENSE`, decided together with cstack's own LICENSE in issue #1).

## 6. Out of scope

- `maintain-verification-skill` (later, see section 3), `create-formal-verification-skill` and `maintain-formal-verification-skill`.
- pstack's model routing (`/setup-pstack`), orchestration mode and multi-model panels (issue #1).
- The 8 principles and the cost rules: separate files in cstack, separate spec.
- Writing the `SKILL.md` files. Cristian implements them in an Orca + OpenCode worktree after this spec is approved.

## 7. Open questions

Top three:

1. **How `verify-template` reaches a consumer.** Spec 0001 has `cstack-install` copy everything except `verify-template`, but an agent can only load a skill that sits in a skills folder. Options: (a) vendor it like the others; (b) run it once from a cstack checkout or `npx skills add` and remove it afterwards; (c) a `cstack-install --with verify-template` flag.
2. **Manual-only invocation.** Upstream marks all three skills `disable-model-invocation: true`. That field is not in the Agent Skills standard, and how OpenCode, Claude Code, Cursor, Codex and pi treat it was not verified here. Keep it, drop it, or rely on a description that says "only when the user asks"?
3. **Where `correct`'s rule table lives.** Upstream keeps it in the agent instruction file. Spec 0001 wants `AGENTS.md` short. Options: in `AGENTS.md`, or a separate file (e.g. `docs/rules.md`) linked from `AGENTS.md`.

Also open: pilot repo (Route or Londinium) for the acceptance runs; whether `correct` may add CI jobs or only propose them; whether `sharpen`'s restatement step stays.

This is a proposal. It has not been implemented.
