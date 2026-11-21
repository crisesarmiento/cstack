> Adapted from pstack 0.15.46 (MIT License, (c) 2026 Lauren Tan), upstream skill
> `create-verification-skill`, `references/feature-map-example/archive-note.md`
> (added for this adaptation; upstream ships two feature files).
> Illustrative example: every command below is fictional and was never
> executed; a real feature file uses only commands discovered in the target
> repository.

# Archive a note

Archive lets a user move a finished note out of the active list, keep it
reachable through `Include archived`, and confirm the stored state from a
second, read-only view.

## Sub-features

- `archive-open` exposes archive from the note view and the list row menu.
- `archive-confirm` requires an explicit confirmation that names the note.
- `archive-list` removes the note from the active list without deleting it.
- `archive-search` hides the note from default search until `Include
  archived` is enabled.
- `archive-cli` archives by ID and prints the stored state.

## How to get to it (user POV)

- Open a note and choose `Archive`.
- Open the row menu on a list entry and choose `Archive note`.
- Run `notes archive <id>` in a terminal.

## Driving it with the repo's e2e runner and notes CLI

Preconditions:

- The baseline preconditions hold and the app is healthy at
  `http://127.0.0.1:4173`.
- A note titled `Grocery list` exists and is unarchived.
- `notes doctor` reports the expected URL and the disposable data directory.

- **Note view entry.** Open `Grocery list` and choose `Archive`. Run
  `npm run test:e2e -- e2e/archive-note.spec.ts -g "note view asks before
  archiving"`. The step passes and its report shows a dialog named
  `Archive note` that names the note.
- **Confirm archive.** Choose `Archive`. Run `npm run test:e2e --
  e2e/archive-note.spec.ts -g "note view archives after confirm"`. The
  step's report shows the active list without `Grocery list`.
- **Row menu entry.** Open the row menu on `Grocery list` and choose
  `Archive note`. Run `npm run test:e2e -- e2e/archive-note.spec.ts -g "row
  menu archives after confirm"`. The same dialog appears, and confirming
  returns to the list without `Grocery list`.
- **Search exclusion.** Search `grocery` with defaults. Run
  `npm run test:e2e -- e2e/archive-note.spec.ts -g "search hides archived by
  default"`. The `No matching notes` status appears.
- **Include archived.** Enable `Include archived` and search `grocery`. Run
  `npm run test:e2e -- e2e/archive-note.spec.ts -g "include archived restores
  the result"`. `Grocery list` appears with its archived marker.
- **CLI entry.** Archive from the terminal. Resolve the note ID first with
  `notes list --format json`, then run `notes archive "$NOTE_ID" --format
  json`. Exit code `0`; stdout shows the note with `"archived": true`.
- **Second view proof.** Read the stored state without mutating it. Run
  `notes show "$NOTE_ID" --format json`. Exit code `0`; stdout contains
  `Grocery list` with `"archived": true`.
- **Proof.** Capture the archived list and the CLI output. Run
  `npm run test:e2e -- e2e/archive-note.spec.ts -g "note view archives after
  confirm"`. The step's report and screenshot under
  `verify-evidence/$RUN_ID/archive-note/` show the list without `Grocery
  list`, and the run log records the `notes show` transcript; the artifacts
  survive cleanup.

## Gotchas

- Archiving is reversible only through `Unarchive`; never restore the list
  by deleting rows.
- `Include archived` persists between searches in the same session. Reset it
  before the next recipe.
- The CLI needs the note ID. Resolve the title to an ID first, or capture
  the ID at seed time.
- Remove the archived fixture during cleanup, but retain its proof
  artifacts.
