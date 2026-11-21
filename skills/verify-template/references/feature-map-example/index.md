> Adapted from pstack 0.15.46 (MIT License, (c) 2026 Lauren Tan), upstream skill
> `create-verification-skill`, `references/feature-map-example/`.
> Illustrative example: every command below is fictional and was never
> executed; a real feature map uses only commands discovered in the target
> repository.

# Example feature map: Notes

This directory is a worked example of the feature map a generated
`verify-<app>` skill ships. A real map is the maintained source for verifying
the user-facing behavior of one real app: read the index before driving, then
use the matching feature file as the recipe. Because this one documents a
fictional notes app, its commands, selectors, paths, and outputs are
illustrative placeholders. A real map contains only commands actually
discovered in the target repository (from its README, scripts, tests, and
entry points), and each `Preconditions:` block names where each command was
found. Nothing here needs to be executed.

## Baseline preconditions

- Launch the app with its own documented command from the repository root
  (illustrative: `npm run dev -- --port 4173`). Treat readiness as usable
  behavior, not a live port: `curl -fsS http://127.0.0.1:4173/notes` returns
  the note list.
- Isolate state per run (illustrative:
  `NOTES_DATA_DIR=$PWD/.verify-data/$RUN_ID`) so concurrent runs never share
  state, and never drive an instance that was not started by this
  verification run.
- Seed the baseline data through the repository's own seeding path
  (illustrative: `notes seed demo`) so notes titled `Quarterly plan` and
  `Grocery list` exist; record the seeding command with the run.
- Confirm instance ownership and build identity before driving (illustrative:
  `notes doctor` reporting the expected URL, data directory, and build
  revision).

## Driving conventions

- Start every recipe from the baseline state unless its preconditions say
  otherwise, and restore seeded data after a mutation.
- Run every command from the repository root in plain shell. Treat each
  command as literal; keep quoted names and flags unchanged.
- Drive the browser surface through the repository's existing end-to-end
  runner invoked as a shell command (illustrative: `npm run test:e2e --
  e2e/<feature>.spec.ts -g "<step>"`), and the terminal surface through the
  repository's own CLI using its documented invocation (illustrative:
  `notes <command>`). Never require an agent's built-in browser or a named
  agent tool.
- Do not remove proof artifacts during cleanup.

## Proof and skip reporting

- Capture the user action and the resulting state, not only the final screen
  or exit code.
- Browser proof includes the runner step report and a screenshot with the app
  identity visible; CLI proof includes the command, stdout, stderr, and exit
  code.
- Mutation proof includes a read-only second view of the stored value.
- Record the feature ID and entry point used with every artifact.
- Write every artifact under `verify-evidence/$RUN_ID/<feature>/`
  (illustrative), a repository-relative directory outside the disposable data
  directory. Cleanup stops only processes this run started and removes only
  disposable state, so evidence survives it.
- Report an unreachable path with the attempted command and the unmet
  precondition. Do not report a skipped entry point as verified through a
  different path.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the
user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with <harness>` starts with `Preconditions:` and uses labeled
   bullets that pair each user action with an exact command and observable
   result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

Keep implementation details out of the map. Name only user paths, stable
handles, required state, commands, and observable proof.

## Features

- [Create a note](./create-note.md) covers browser and CLI creation,
  cancellation, persistence, and cleanup.
- [Search notes](./search.md) covers toolbar, keyboard, and CLI search with
  matching, empty, and clear states.
- [Archive a note](./archive-note.md) covers archiving from the note view and
  the CLI, list updates, and search exclusion.
