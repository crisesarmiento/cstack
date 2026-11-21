> Adapted from pstack 0.15.46 (MIT License, (c) 2026 Lauren Tan), upstream skill
> `create-verification-skill`, `references/feature-map-example/search.md`.
> Illustrative example: every command below is fictional and was never
> executed; a real feature file uses only commands discovered in the target
> repository.

# Search notes

Search lets a user find notes by title or body text, inspect a matching note,
and distinguish no matches from an unavailable search.

## Sub-features

- `search-open` opens search from each supported browser entry point.
- `search-match` returns title and body matches without changing note data.
- `search-open-result` opens a result in the note editor.
- `search-empty` shows a complete empty state for a query with no matches.
- `search-clear` removes the query and restores the recent-notes view.
- `search-cli` returns the same matching notes from the terminal.

## How to get to it (user POV)

- Choose the `Search` button in the browser toolbar.
- Press `/` in the browser while focus is outside an editable field.
- Run `notes search <query>` in a terminal.

## Driving it with the repo's e2e runner and notes CLI

Preconditions:

- The baseline preconditions hold and the app is healthy at
  `http://127.0.0.1:4173`.
- The disposable data directory contains `Quarterly plan` with body text
  `Draft budget`.
- `notes doctor` reports the expected URL and data directory.

- **Toolbar entry.** Choose the `Search` button. Run `npm run test:e2e --
  e2e/search.spec.ts -g "toolbar opens search"`. The step passes with a
  dialog named `Search notes` focused on its searchbox.
- **Keyboard entry.** Close the dialog, focus the page, and press `/`. Run
  `npm run test:e2e -- e2e/search.spec.ts -g "slash opens search"`. The same
  dialog appears and the page does not insert a slash.
- **Title match.** Type `quarterly`. Run `npm run test:e2e --
  e2e/search.spec.ts -g "title match"`. The `Search results` list contains
  `Quarterly plan` and does not contain `Grocery list`.
- **Body match.** Replace the query with `budget`. Run `npm run test:e2e --
  e2e/search.spec.ts -g "body match"`. `Quarterly plan` remains visible with
  a body-match excerpt.
- **Open result.** Choose `Quarterly plan`. Run `npm run test:e2e --
  e2e/search.spec.ts -g "open result"`. The dialog closes and the editor
  heading reads `Quarterly plan`.
- **Empty state.** Reopen search and enter `volcano`. Run `npm run test:e2e
  -- e2e/search.spec.ts -g "empty state"`. A status named `No matching
  notes` appears after search completes.
- **Clear query.** Choose `Clear search`. Run `npm run test:e2e --
  e2e/search.spec.ts -g "clear query"`. The searchbox is empty and the
  `Recent notes` region replaces the result list.
- **CLI match.** Search from the terminal. Run `notes search "quarterly"
  --format json`. Exit code `0`; stdout contains one object whose title is
  `Quarterly plan`.
- **CLI miss.** Search for an absent value. Run `notes search "volcano"
  --format json`. Exit code `0`; stdout is `[]`.
- **Proof.** Capture the populated result state. Run `npm run test:e2e --
  e2e/search.spec.ts -g "title match"`. The step's report and screenshot
  under `verify-evidence/$RUN_ID/search/` identify the app, the query
  `quarterly`, and `Quarterly plan`; the artifacts survive cleanup.

## Gotchas

- Pressing `/` while the editor or searchbox has focus inserts text instead
  of opening search.
- Results update after a short debounce. The steps wait for the results list
  or the empty status, never a fixed sleep.
- Archived notes are excluded unless the user enables `Include archived`.
- The CLI defaults to human-readable output. Use `--format json` for stable
  assertions.
- Opening a result changes browser state. Reopen search before proving
  another query.
