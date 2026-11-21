# Spec: cstack structure and versioning

- **Date:** 21/11/2026 (America/Cordoba)
- **Issue:** [#1](https://github.com/crisesarmiento/cstack/issues/1) (opened 21/11/2026 09:12 ART; spec v0.1)
- **Status:** proposal, not implemented. Decision 2026-11-21: `.agents/skills/` canonical (see issue #1 comment https://github.com/crisesarmiento/cstack/issues/1#issuecomment-7062625489)
- **Repo:** https://github.com/crisesarmiento/cstack (public; as of 21/11/2026, only a one-line README; no license yet)
- **The repo and the machines were not modified for this research.** Cristian implements with Orca + OpenCode; this document is the spec only.

Sources consulted on 21/11/2026: OpenCode [Skills](https://opencode.ai/docs/skills/), [Instructions](https://opencode.ai/docs/instructions/), [Agents](https://opencode.ai/docs/agents/), [Commands](https://opencode.ai/docs/commands/), [Config](https://opencode.ai/docs/config/), [Plugins](https://opencode.ai/docs/plugins/); slim v3.0.7 [`docs/skills.md`](https://github.com/alvinunreal/oh-my-opencode-slim/blob/v3.0.7/docs/skills.md) and [`docs/project-local-customization.md`](https://github.com/alvinunreal/oh-my-opencode-slim/blob/v3.0.7/docs/project-local-customization.md); [Agent Skills spec](https://agentskills.io/specification) and [where to scan](https://github.com/agentskills/agentskills/blob/main/docs/client-implementation/adding-skills-support.mdx); [Claude Code skills](https://code.claude.com/docs/en/skills) and [memory / AGENTS.md](https://code.claude.com/docs/en/memory); [Cursor skills](https://cursor.com/docs/skills) and [rules / AGENTS.md](https://cursor.com/docs/rules); [Codex skills](https://learn.chatgpt.com/docs/build-skills) and [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md); [Pi skills](https://docs.pi.dev/latest/skills) and [configuration](https://docs.pi.dev/latest/configuration); [Gemini CLI skills](https://geminicli.com/docs/cli/using-agent-skills/) (page updated 30/4/2026) and [GEMINI.md](https://geminicli.com/docs/cli/gemini-md/) (18/6/2026); [Amp skills](https://ampcode.com/docs/customize/skills) and [AGENTS.md](https://ampcode.com/docs/customize/agents-md); [Copilot skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills) and [custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions); [`npx skills` / vercel-labs/skills](https://github.com/vercel-labs/skills) ([commands](https://github.com/vercel-labs/skills/blob/main/docs/commands.md), [agents](https://github.com/vercel-labs/skills/blob/main/docs/agents.md)); pstack 0.15.46; Superpowers [`docs/README.opencode.md`](https://github.com/obra/superpowers/blob/main/docs/README.opencode.md); Compound Engineering (local copy, 21/11).

## 1. What this spec must settle

cstack is a versioned pack (skills, principles, slim presets, cost rules). It is designed first for OpenCode 2.3 + oh-my-opencode-slim 3.0.7, reusable in Londinium (Godot/GDScript) and Route (TS, Biome), and **eventually public**. Rules are enforced by structure, not by memory. Before a project adopts it, we must settle the **tree, versioning, how a version is pinned, and which folder the install writes to**, so skills load in more than one agent.

Issue #1 already fixes the v0.1 contents (`correct`, `verify-template`, `sharpen`, 8 principles, cost rules). This spec does not reopen that.

## 2. How OpenCode 2.3 (and slim 3.0.7) loads files

### Skills

Confirmed project path: `.opencode/skills/<id>/SKILL.md` (directory form; the ID is the folder name, case-sensitive). A loose `.md` file at the root of `skills/` is also accepted. Docs: [Skills](https://opencode.ai/docs/skills/).

Other automatic paths:

| Scope | Path |
| --- | --- |
| Global | `~/.config/opencode/skills` |
| Global compatibility | `~/.claude/skills`, `~/.agents/skills` |
| Project | `.opencode/skills` (from the cwd up to the project root, every level) |
| Project compatibility | `.claude/skills`, `.agents/skills` |

More sources can be added with the `skills` array in `opencode.json(c)` (relative paths **from the active working directory**, `~/`, absolute paths, or an HTTP catalog with `index.json` plus a `version` field). Arrays are **combined**, not replaced.

Precedence (the source registered **later** wins for the same ID): built-in → `.claude` → `.agents` → `~/.config/opencode/skills` → `.opencode/skills` (from the project root toward the cwd) → explicit `skills` entries. The project overrides the global source.

The model sees only the ID, name, and description. It loads the body with the `skill` tool or with `@skill-id`.

### AGENTS.md and `instructions`

OpenCode loads `~/.config/opencode/AGENTS.md`, then each `AGENTS.md` from the workspace upward. If the workspace is **outside `$HOME`**, discovery stops at the project root. If the workspace is **outside the project root, only the global file is loaded** ([Instructions](https://opencode.ai/docs/instructions/)). Conflicts are not resolved: files are concatenated. The `instructions` array in `opencode.json` loads **afterward**. `OPENCODE_DISABLE_PROJECT_CONFIG=1` skips project files.

A Git worktree *is* the root of that checkout, so a committed `AGENTS.md` should load. **This has not been verified in an Orca worktree** (`~/orca/workspaces/<project>/…`).

### Agents, commands, config

- Agents: `~/.config/opencode/agents/<name>.md` and `.opencode/agents/<name>.md` ([Agents](https://opencode.ai/docs/agents/)).
- Commands: `~/.config/opencode/commands/` and `.opencode/commands/` (project overrides global; a nearer path overrides an ancestor) ([Commands](https://opencode.ai/docs/commands/)).
- Config: `~/.config/opencode/opencode.json(c)` and, in the project, `opencode.json(c)` or `.opencode/opencode.json(c)`. Search walks from the cwd to the filesystem root. Direct `opencode.json` files are merged first (outer to inner), then files under `.opencode/` ([Config](https://opencode.ai/docs/config/)). **There is no `.opencode/rules/` loader** like Cursor has.

### slim 3.0.7

Project preset: `.opencode/oh-my-opencode-slim.json` or `.jsonc` (`.jsonc` wins if both exist). On v2 hosts, discovery walks **past** the worktree root, up to the filesystem root. `~/.opencode` is a project layer for paths under `$HOME`.

An agent's `skills` field in a preset is a **permission** (which skills it may activate), not the place the files live: `"*"`, an explicit list, or `"!name"` to deny. If a layer defines `skills`, it **replaces** the inherited list. To add or remove without replacing: `skills_add`, `skills_remove` (remove wins). `skills_include_local: true` adds valid `SKILL.md` files from the project's and ancestors' `.opencode/skills` and `.agents/skills` trees, before remove is applied ([skills.md](https://github.com/alvinunreal/oh-my-opencode-slim/blob/v3.0.7/docs/skills.md) and [project-local-customization.md](https://github.com/alvinunreal/oh-my-opencode-slim/blob/v3.0.7/docs/project-local-customization.md), tag v3.0.7).

Caution: a stray `.opencode/` under `~/`, `~/orca/`, or `~/Projects/` can be picked up on that walk. Do not put cstack config there.

## 3. How pstack, Superpowers, and Compound Engineering version

- **pstack 0.15.46:** tree is `skills/<id>/SKILL.md`, `agents/`, and `plugin.json` with `"version"`. **There is no CHANGELOG.** Model routing is written separately (`pstack-models.mdc`) and does not migrate on its own. Use it as a shape reference, not as a distribution model (it is a Cursor/Claude Code plugin, not an OpenCode plugin).
- **Superpowers:** `skills/` plus a `package.json` with semver (the docs cite pinning `v7.0.2`). On OpenCode 2 it installs as a plugin and is pinned with a tag or commit: `plugins: ["superpowers@git+https://github.com/obra/superpowers.git#v7.0.2"]` ([README.opencode.md](https://github.com/obra/superpowers/blob/main/docs/README.opencode.md), consulted 21/11). The plugin registers the skills directory; a JS entry is required. Older symlinks are being left behind.
- **Compound Engineering:** the local plugin copy (21/11) has `package.json` and `plugin.json` (version **3.29.0** in that copy; a newer version may exist; the remote tag was not re-checked), `CHANGELOG.md`, and `skills/`. Same model: manifest + changelog + plugin.

Takeaway: skills live in `skills/<id>/SKILL.md`, a version lives in a manifest, there is a CHANGELOG, and the consumer pins the version. Do not copy pstack's missing changelog.

## 4. Cross-agent compatibility

The [Agent Skills](https://agentskills.io/specification) specification (consulted 21/11/2026) defines the **contents** of a skill (`SKILL.md` with `name` + `description` frontmatter, plus `scripts/`, `references/`, `assets/`). **It does not mandate the folder** the skill lives in. The cross-client convention, documented for client implementers, is [`.agents/skills/`](https://github.com/agentskills/agentskills/blob/main/docs/client-implementation/adding-skills-support.mdx) (project) and `~/.agents/skills/` (user).

### Matrix (project / user-level / AGENTS.md)

Official docs, 21/11/2026. "Standard" means the agent accepts `SKILL.md` with `name`/`description`.

| Agent | Project skills | User-level skills | Reads `.agents/skills/`? | AGENTS.md | Standard |
| --- | --- | --- | --- | --- | --- |
| **OpenCode 2.3** | `.opencode/skills/` (native) **and**, as compatibility paths, `.agents/skills/`, `.claude/skills/` | `~/.config/opencode/skills`; compatibility `~/.agents/skills`, `~/.claude/skills` | **Yes** ([Skills](https://opencode.ai/docs/skills/)). Precedence: `.opencode/skills` wins for the same ID | **Yes.** Falls back to `CLAUDE.md` if there is no `AGENTS.md`; a symlink between the two is loaded once | Yes (accepts standard fields; does not require them at runtime) |
| **Claude Code** | `.claude/skills/` | `~/.claude/skills/` | **Not documented.** The skills docs (21/11) only list `.claude/skills/`. A September 2026 issue ([#31005](https://github.com/anthropics/claude-code/issues/31005), comment 19/9/2026) said v2.1.277 added `AGENTS.md` but not `.agents/skills/`. A later change was not confirmed | **Yes, conditional:** if there is no `CLAUDE.md` / `CLAUDE.local.md` in the cwd or above it (v2.1.277+). If `CLAUDE.md` exists, it wins, unless the config is `claude-md-and-agents-md` | Yes, with its own extensions |
| **Cursor** | `.agents/skills/` and `.cursor/skills/`; compatibility `.claude/skills/`, `.codex/skills/` | `~/.agents/skills/`, `~/.cursor/skills/`; compatibility `~/.claude/`, `~/.codex/` | **Yes** ([docs](https://cursor.com/docs/skills/)) | **Yes** (root and nested) | Yes |
| **Codex CLI** | `.agents/skills/` (from the cwd up to the repo root). `.codex/skills` is legacy and still works | `~/.agents/skills/`; `/etc/codex/skills` for admin. `~/.codex/skills` is legacy | **Yes** — this is the current official path ([build-skills](https://learn.chatgpt.com/docs/build-skills)) | **Yes** (repo `AGENTS.md` and `~/.codex/AGENTS.md`) | Yes |
| **pi** (docs.pi.dev) | `.agents/skills/` (cwd → repo root) and `.pi/skills/` | `~/.agents/skills/` and `~/.pi/agent/skills/` (the default agent directory is `~/.pi/agent`) | **Yes** ([skills](https://docs.pi.dev/latest/skills)) | **Yes** (also accepts `CLAUDE.md` as a context file) | Yes |
| **Gemini CLI** | `.agents/skills/` or `.gemini/skills/` | `~/.agents/skills/` or `~/.gemini/skills/` | **Yes** (it calls this an "alias") | **Not by default.** The default file is `GEMINI.md`. `AGENTS.md` is included if `settings.json` lists that name in `context.fileName` ([GEMINI.md](https://geminicli.com/docs/cli/gemini-md/), 18/6/2026) | Yes |
| **Amp** | `.agents/skills/` (it also scans `.claude/skills/`) | `~/.config/agents/skills/`, `~/.agents/skills/`, `~/.config/amp/skills/`, plus Claude locations | **Yes** | **Yes.** If there is no `AGENTS.md`, it falls back to `AGENT.md` or `CLAUDE.md` | Yes |
| **GitHub Copilot CLI** | `.agents/skills/`, `.claude/skills/`, or `.github/skills/` | `~/.agents/skills/` or `~/.copilot/skills/` | **Yes** | **Yes**, along with `.github/copilot-instructions.md`, `CLAUDE.md`, `GEMINI.md` | Yes |

Direct answer: **yes, OpenCode 2.3 reads `.agents/skills/` and `.claude/skills/`** (compatibility paths). If a skill lives only in `.opencode/skills/`, Cursor, Codex, pi, Gemini, Amp, and Copilot **will not** see it (none of their official docs list `.opencode/skills/`).

### How other packs install

- **`npx skills`** ([vercel-labs/skills](https://github.com/vercel-labs/skills), consulted 21/11): installs into the project by default. For OpenCode, Cursor, Codex, pi, Gemini, Amp, and Copilot, the project path it declares is **`.agents/skills/`**. Claude Code goes to **`.claude/skills/`**. The default is a **symlink** from each agent folder to a canonical copy; `--copy` if symlinks are not available. It detects installed agents; `-a` selects them; a version can be pinned with `npx skills add owner/repo@v1.2.3`.
- **pstack:** a Cursor plugin plus a Claude Code adapter. It does not target `.agents/`.
- **Superpowers:** a per-harness plugin (on OpenCode it registers skills; it does not copy them into several folders). OpenCode project docs: `.opencode/skills/`.

## 5. Proposed tree (the `cstack` repo)

File and folder names are in English. No secrets, `.env` files, or keys.

```
README.md                 # what it is, how to install a pinned version, link to the issue
LICENSE                   # pending (the issue suggests MIT + attribution to pstack)
CHANGELOG.md              # Keep a Changelog; one entry per release
VERSION                   # raw semver, one line, e.g. 0.1.0
cstack.json               # { "name": "cstack", "version": "0.1.0" } — version source
skills/
  correct/SKILL.md        # repeated mistake → lint/types/test (no pstack model routing)
  sharpen/SKILL.md        # deepen the prompt, do not enlarge it
  verify-template/        # template so a project can generate verify-<app>
    SKILL.md
principles/
  PRINCIPLES.md           # the 8 principles, one checklist file
presets/                  # slim templates, no secrets or keys
  londinium.json
  route.json
rules/
  cost-and-models.md      # text of the cost rules (not an OpenCode loader)
templates/
  AGENTS.md               # short context; not the checkable rules
install/
  README.md               # how to adopt and upgrade
  cstack-install          # script: copies a tagged version into .agents/skills/ (+ symlinks)
.github/                  # optional, later: CI for cstack itself
```

v0.1 has **no** OpenCode `agents/` or `commands/` (slim already covers the roles).

### What is global vs per-project

| Thing | Where it lives | Who pins it |
| --- | --- | --- |
| cstack source | `~/Projects/cstack` on Mac and Omarchy, and GitHub | The clone may sit on `main`; projects do not depend on that branch at runtime |
| Shared skills (`correct`, `sharpen`, …) | Vendored into the consumer's `.agents/skills/` (see §6 and §7) | The project, to a tag |
| `verify-<app>` | In the project only (generated from the template) | The project |
| Live preset | The project's `.opencode/oh-my-opencode-slim.json` | The project; cstack only ships a template |
| Repo `AGENTS.md` | Consumer root (canonical). Relative symlink `CLAUDE.md` → `AGENTS.md` | The project |
| `~/.config/opencode/skills` | Do not use for cstack in production | No per-project pin |

## 6. How a project pins and upgrades

Files in the **consumer**, committed:

```
.agents/skills/
  correct/SKILL.md          # canonical copy of that version (do not edit)
  sharpen/SKILL.md
.claude/skills/
  correct -> ../../.agents/skills/correct   # relative symlink (Claude Code does not read .agents, docs 21/11)
  sharpen -> ../../.agents/skills/sharpen
.opencode/
  cstack.lock.json          # { "version": "0.1.0", "tag": "v0.1.0" }
  oh-my-opencode-slim.json  # project preset; skills_add / skills_include_local
AGENTS.md                   # canonical
CLAUDE.md -> AGENTS.md      # relative symlink; OpenCode loads it once
```

There is no need to also copy into `.opencode/skills/`: OpenCode and slim 3.0.7 (`skills_include_local`) already read `.agents/skills/`. Duplicating the same ID in both folders only confuses precedence.

Install, first-party option:

```text
cstack-install --version v0.1.0 --project /path/to/repo
```

The script copies `skills/` (except `verify-template`) into **`.agents/skills/`**, creates the **relative symlinks** under `.claude/skills/<id>` (a fixed layout, not "only if Claude is detected on this machine": the shared repo must work for anyone who clones it), writes `cstack.lock.json`, and does not overwrite `verify-<app>` or the live preset. An upgrade is the same command with a new tag, plus a PR in the consumer.

Install, public compatible option:

```text
npx skills add crisesarmiento/cstack@v0.1.0
```

This requires the cstack repo to expose `skills/` at the root (already in the tree). `npx skills` installs to `.agents/skills/` for OpenCode/Cursor/Codex/pi/Gemini/Amp/Copilot and to `.claude/skills/` for Claude Code; the default is a symlink. Use `--copy` if needed. `-a` selects agents; otherwise it detects the agents installed on **that** machine (for a public repo it is better to commit the fixed layout above, not the result of a local auto-detect).

`--agents` on `cstack-install` may exist for rare cases, but the default for a committed install is the portable layout (`.agents/skills/` + the Claude symlink), not local detection.

Vendored copies are not edited: repo-specific work goes in a skill with a **different ID** (e.g. `verify-londinium`), also under `.agents/skills/`.

In slim, do not redefine the whole `skills` list if an inherited list already exists. Use `skills_add: ["correct", "sharpen"]` (and the `verify-*` skill when it exists) or `skills_include_local: true` (it includes `.agents/skills/` and `.opencode/skills/`). Do not overwrite the preset with an accidental `"*"` on the fixer.

Orca worktrees: files and **relative symlinks** live inside the repo, so a worktree under `~/orca/workspaces/<project>/…` gets them with the checkout. An absolute symlink to `~/Projects/cstack` does not. Windows is not a requirement now.

`GEMINI.md`: not created by default (Gemini CLI does not read `AGENTS.md` until someone configures it). If a project uses Gemini CLI, it can add `GEMINI.md -> AGENTS.md`, knowing that if `AGENTS.md` is also enabled in `context.fileName` the file may load twice. This stays optional, not part of the default layout.

## 7. Distribution: A/B/C

| | A. Copy/sync (`cstack-install --version vX`) | B. git submodule | C. OpenCode plugin |
| --- | --- | --- | --- |
| How it pins | `cstack.lock.json` + files in `.agents/skills/` (+ Claude symlink) | submodule at a tag/SHA | `plugins: ["…cstack.git#v0.1.0"]` ([Plugins](https://opencode.ai/docs/plugins/); a full hash stays pinned) |
| Orca worktrees | Yes: it travels with the checkout | Fragile: each worktree needs `git submodule update --init` | The pin is in `opencode.json`; the package lives in the OpenCode cache, not in the Godot repo |
| Mac + Omarchy | A `git pull` of the consumer is enough | The same, plus the submodule | The plugin must be installed/cached on both machines |
| Londinium / Route | No npm in Godot | Native git, more ceremony | A JS entry is required (like Superpowers). That is more than v0.1 needs |
| Cons | Vendored copies must not be edited; a script must be maintained | Known pain with worktrees; an extra path | Large scope now; cache updates sometimes get stuck (documented by Superpowers) |

**Do not use:** a symlink to `~/Projects/cstack`. There is no per-project pin (every project sees whatever branch is checked out). A relative symlink breaks under `~/orca/workspaces/…`. An absolute symlink to `~/Projects/cstack` would work on both machines, but still has no per-repo versioning.

**Recommendation: A**, with the target **`.agents/skills/`** (not only `.opencode/skills/`). Then OpenCode, Cursor, Codex, pi, Gemini, Amp, and Copilot read the same checkout; Claude Code enters through the relative symlink. For someone installing cstack from the outside, `npx skills add crisesarmiento/cstack@vX` is a documented, compatible path. C (OpenCode plugin) remains post-1.0. B (submodule) is not the default.

On *where* to install, in short:

- **A (recommended):** canonical `.agents/skills/` + a relative symlink `.claude/skills/<id>`.
- **B:** copy into every vendor folder (`.opencode`, `.cursor`, `.codex`, `.pi`, `.gemini`, `.github`, …). This duplicates files and they drift apart.
- **C:** `.opencode/skills/` only. This is enough for Cristian's current stack; it **does not** work when the pack is shared publicly.

## 8. Semver, CHANGELOG, and releases

The version lives in `VERSION` and `cstack.json`. Tags are `vMAJOR.MINOR.PATCH`. Start at `0.1.0`. While the version is `0.x`, a breaking change bumps **MINOR** and is called out in the changelog. Only at `1.0.0` does a breaking change become MAJOR.

| Kind | What triggers it |
| --- | --- |
| **MAJOR** (or MINOR on 0.x) | Removing or renaming a skill ID; changing a skill contract or a cost rule in an incompatible way; changing the paths the installer writes |
| **MINOR** | Adding a skill, a principle, or a preset template, without breaking what came before |
| **PATCH** | Clarifications, typos, examples, docs, fixes that do not change the contract |

`CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/): `Added`, `Changed`, `Removed`, `Fixed`, with a date and a link to the tag. A release = merge to `master` + tag `vX.Y.Z` (a GitHub Release is optional). Do not publish a tag without a changelog entry.

## 9. Presets without secrets

`presets/` contains only model IDs (`provider/model` or `#variant`), skill grants, and comments. No API keys, `.env` files, tokens, or headers. The **live** preset stays in the project (Londinium already follows this pattern). The template is merged by hand or by the installer in a non-destructive mode (if the file already exists, it is not overwritten; a `.example` is left instead).

Model IDs are not secrets, but they change with the catalog (Go, OpenAI, and so on). Templates document the intent of each role; the project fills in the slugs it pays for.

## 10. Where each rule is enforced

Same as issue #1 (from pstack's `correct` idea):

1. **Checkable** → lint, types, tests, a hook, or CI. The error names the fix. In Route, Biome/tests; in Londinium, whatever CI/headless already exists.
2. **Judgement** → a short skill (`correct`, `sharpen`).
3. **Context** → `AGENTS.md` (build commands, architecture, "look at evidence before the diff"). Keep it short. This is not the place for a rule that can be checked.

A rule is added only after the same mistake has happened **twice**, with proof that the check fails on that past mistake.

Cost rules (OpenRouter/NVIDIA free routes only, no paid fallbacks; Grok never in OpenCode automatic chains; a Decision approved before implementation) do not live only in `AGENTS.md`. They go into the preset (do not list those models in the chains) and, when possible, into a CI check that fails if the slim JSON puts `grok` or a paid route on an automatic agent. The text in `rules/cost-and-models.md` is the specification, not the enforcement.

## 11. Open questions

Still from issue #1:

- Pilot in Route or Londinium first?
- MIT LICENSE with attribution to pstack?

New, and they do not block the tree:

- `skills_include_local: true`, or only an explicit `skills_add` in the preset?
- Also offer the OpenCode plugin later (post-1.0)?
- Verify in a real Orca worktree that `.agents/skills/` and `AGENTS.md` load (the docs say they should; this was not confirmed here in practice).
- Does Claude Code already read `.agents/skills/` in some version after September 2026? If it does, the symlink may no longer be needed; official docs do not list it today.
- Include `GEMINI.md -> AGENTS.md` in the default layout, or leave it optional?

This is a proposal. It has not been implemented.
