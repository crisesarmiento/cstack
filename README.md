# cstack

Cristian's versioned AI coding stack: short skills, a principles checklist,
cost rules and an optional OpenCode/oh-my-opencode-slim preset. Adapted from
pstack 0.15.46 (MIT); see [NOTICE.md](NOTICE.md) and [LICENSE](LICENSE).

The skills are agent-agnostic: OpenCode, Claude Code, Cursor, Codex and pi use
the same files. Only the optional slim preset is harness-specific.

## Install a pinned version

After the release tag is published, run the installer from a cstack Git checkout
(Git and a POSIX shell are required):

```sh
./install/cstack-install --version v0.1.1 --project /path/to/project
```

If `install/` is on your `PATH`, the equivalent command is:

```sh
cstack-install --version v0.1.1 --project /path/to/project
```

It copies `correct` and `sharpen` from the requested tag to `.agents/skills/`,
creates relative `.claude/skills/<id>` symlinks, and records the version, tag
and resolved commit in `.opencode/cstack.lock.json`. Commit those files in the
consumer repository: the pin and links then travel with every worktree.
Re-run with a new tag to upgrade; differing skill directories require an explicit
`--force`. See [installer usage and checks](install/README.md).

The public compatible alternative is:

```sh
npx skills add crisesarmiento/cstack@v0.1.1
```

To install only the shared skills, add `-s correct -s sharpen`. This alternative
uses the skills CLI's agent selection and layout; it does not write cstack's
lock file. Review and commit the canonical copies and relative Claude links
instead of relying on machine-specific detection.

`verify-template` is a one-time generator, not a vendored shared skill.
Run it from a cstack checkout or select it through `npx skills`; commit only
the generated `.agents/skills/verify-<app>/` and its relative Claude symlink.
The installer does not copy the generator, presets or context files.

## Adopt in a project

1. Get the project's Decision approved before implementation or rollout.
2. Install the pinned shared skills.
3. Adapt [templates/AGENTS.md](templates/AGENTS.md) to real build/test commands.
   Bring [rules/](rules/) and [principles/](principles/) into the project, or
   change the template's links to the chosen pinned location.
   Keep `AGENTS.md` canonical and commit `CLAUDE.md -> AGENTS.md`.
4. For OpenCode with slim 3.0.7, manually merge the
   [preset template](presets/) into the project's live preset. Fill model IDs
   only after checking the [cost policy and enforcement](rules/cost-and-models.md).
   Review the [agent permission rules](rules/agent-permissions.md) for every
   agent: exact-command shell allows only, with interactive verification.
   Do not overwrite an existing preset or inherit unreviewed fallback routes.
5. Generate a project verification skill when needed; review evidence before
   the diff. No global configuration or per-machine cstack symlinks are needed.

## Contents and status

- [Skills](skills/): `correct`, `sharpen`, and `verify-template`.
- [Eight principles](principles/PRINCIPLES.md): one implementation checklist.
- [Rules](rules/cost-and-models.md): cost, routing and Decision enforcement.
  [Agent permissions](rules/agent-permissions.md): exact-command shell allows
  and consumer-owned interactive verification; only the orchestrator runs
  verification; no automated enforcement yet.
- [Versioning and layout spec](docs/specs/0001-structure-and-versioning.md),
  [skill contracts](docs/specs/0002-first-skills.md),
  [pilot results for v0.1.0-pilot.1 in Londinium](docs/pilots/v0.1.0-pilot.1-londinium.md),
  and [changelog](CHANGELOG.md).

Scope and approved decisions: [issue #1](https://github.com/crisesarmiento/cstack/issues/1).
[Pilot results in Londinium](docs/pilots/v0.1.0-pilot.1-londinium.md)
([#8](https://github.com/crisesarmiento/cstack/issues/8))
confirm loading in OpenCode, Claude Code and Codex, and record later
`correct` evidence (including a fail-then-pass check in Londinium #398).
Cursor and pi loading, and a second-agent `verify-template` run, remain
unverified; this release does not claim otherwise.

Versions live in `VERSION` and `cstack.json`; tags use `vMAJOR.MINOR.PATCH`.
Breaking changes during `0.x` bump MINOR. A release requires a changelog entry
and a separately published tag after merge; preparing v0.1.0 does not create it.
