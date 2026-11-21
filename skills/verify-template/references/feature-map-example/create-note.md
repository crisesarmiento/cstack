> Adapted from pstack 0.15.46 (MIT License, (c) 2026 Lauren Tan), upstream skill
> `create-verification-skill`, `references/feature-map-example/create-note.md`.
> Illustrative example: every command below is fictional and was never
> executed; a real feature file uses only commands discovered in the target
> repository.

# Create a note

Create note lets a user save a titled note from the browser or CLI, cancel an
unfinished draft, and confirm the saved note from a second user-facing view.

## Sub-features

- `create-open` opens a blank editor from each browser entry point.
- `create-save` persists a title and body.
- `create-cancel` discards an unfinished browser draft.
- `create-cli` creates the same note shape from the terminal.

## How to get to it (user POV)

- Choose the `New note` button in the browser toolbar.
- Press `n` in the browser while focus is outside an editable field.
- Run `notes create --title <title> --body <body>` in a terminal.

## Driving it with the repo's e2e runner and notes CLI

Preconditions:

- The baseline preconditions hold and the app is healthy at
  `http://127.0.0.1:4173`.
- No note is titled `Release checklist`.
- `notes doctor` reports the expected URL and the disposable data directory.

- **Open editor.** Choose `New note`. Run `npm run test:e2e --
  e2e/create-note.spec.ts -g "toolbar opens a blank editor"`. The step passes
  and its report shows a form named `Note editor` with focus in the `Title`
  textbox.
- **Enter content.** Type the title and body. Run `npm run test:e2e --
  e2e/create-note.spec.ts -g "editor enables save after input"`. The step
  fills `Title` with `Release checklist` and `Body` with `Tag and publish`,
  and its report shows the `Save note` button enabled.
- **Save note.** Choose `Save note`. Run `npm run test:e2e --
  e2e/create-note.spec.ts -g "save persists the note"`. The step's report
  shows a status named `Note saved` and the heading `Release checklist`.
- **Confirm persistence.** Return to the note list and reopen the note. Run
  `npm run test:e2e -- e2e/create-note.spec.ts -g "list reopens the saved
  note"`. The step's report shows the editor with both saved values, read
  from the stored note, not the draft.
- **Cancel draft.** Open a new note, enter `Discard me`, and choose
  `Cancel`. Run `npm run test:e2e -- e2e/create-note.spec.ts -g "cancel
  discards the draft"`. The step's report shows the note list with no
  `Discard me` entry.
- **CLI entry.** Create a second note. Run `notes create --title "CLI note"
  --body "Created from terminal" --format json`. Exit code `0`; stdout
  contains the new note ID and title.
- **Proof.** Reopen both saved notes from `All notes`. Run
  `npm run test:e2e -- e2e/create-note.spec.ts -g "list shows both saved
  notes"`. The step's report and screenshot under
  `verify-evidence/$RUN_ID/create-note/` show `Release checklist` and
  `CLI note`; the artifacts survive cleanup.

## Gotchas

- Pressing `n` while a textbox has focus types the character instead of
  opening a new editor.
- Titles are trimmed on save. Assert the rendered title, not the draft input
  value.
- A save status alone is insufficient proof. Reopen the note from the list.
- Remove `Release checklist` and `CLI note` during fixture cleanup, but
  retain their proof artifacts.
