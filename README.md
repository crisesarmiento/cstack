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

## Mechanical checks

The `Mechanical checks` CI workflow runs two dependency-free checks (Python 3,
Git and a POSIX shell are required):

- **Personal paths:** scan working copies of Git-tracked files and symlink text
  for absolute Linux/macOS home paths. Diagnostics identify the file and line,
  not its contents. Known sensitive paths are rejected without reading them;
  untracked files and symlink destinations are not read.
- **Skill lock and symlinks:** validate a consumer's
  `.opencode/cstack.lock.json` version, tag and commit against a local source
  repository, compare vendored skills and executable modes with the pinned
  source, and require relative `.claude/skills/` symlinks. Consumer-owned skills
  are preserved; `verify-template` is not installed.

From the cstack repository root, run the same fixture suites as CI:

```sh
python3 -B checks/test-mechanical-checks.py paths
python3 -B checks/test-mechanical-checks.py skills
```

The paths suite also scans this checkout. The skills suite uses the real
installer and producer **HEAD** in an isolated, offline Git source and consumer;
commit relevant source changes before running it. Both suites include expected
failures and return zero only when every outcome matches. cstack is the producer,
so it does not need an installed consumer lock of its own.

To check a checkout or an existing pinned consumer directly:

```sh
python3 -B checks/check-no-personal-paths.py --repo /path/to/project
python3 -B checks/check-skills-lock.py --source /path/to/cstack --project /path/to/project
```

The source must already contain the consumer's pinned release tag; the checker
does not fetch it. For the existing installer and preset checks, also run:

```sh
sh install/test-cstack-install.sh
python3 presets/checks/check_presets.py --scan presets
python3 presets/checks/check_presets.py --self-test presets/checks/fixtures
```

The separate [skills model-neutrality workflow](.github/workflows/skills-model-neutrality.yml)
checks model/vendor names under `skills/`. Its `run` block is Bash and can be
run locally unchanged from the repository root.

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
