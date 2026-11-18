# Progress

## Session 2
- Implemented F02 (`list`): prints `<id> [ ] <title>` / `[x]` in id order, or `No tasks`.
  Added `format_line` helper for reuse by later features.
- Marked F02 passing in feature_list.json.

## Next
- F03 (done), then F04 through F12 in order.
- Task-line suffixes (priority, tags, due) are not yet implemented; extend `format_line` when adding F05-F07.

## Session 3
- Implemented F03 (`done ID`): marks task done, prints `Done <id>`; unknown id -> `No such task: <id>` exit 1.
- Marked F03 passing.

## Next
- F04 (delete) onward, in order. Add a `find_task` helper if useful.

## Session: F04 delete
- Implemented `delete ID` (removes task, prints `Deleted <id>`, unknown id -> `No such task`).
- Ids are not reused because `next_id` is persisted.
- Next: F05 (priority).

## Session: F05 priority
- Added `parse_options` helper (valued options like `--priority`, `--sort`; unknown `--x` is an error).
- `add TITLE --priority high|medium|low` (default medium, stored as `priority`); invalid -> `Invalid priority: <v>` exit 1.
- `format_line` appends `(high)`/`(low)`; medium has no suffix. Tasks lacking `priority` default to medium.
- `list --sort priority` stable-sorts high, medium, low with id ties.
- Marked F05 passing.
- Next: F06 (tags). Add `--tag` (repeatable) to add via parse_options, store `tags` list, suffix ` #a #b` after priority, `list --tag X` filter (combine with --sort).

## Session: F06 tags
- `add TITLE --tag X` is repeatable (stored as `tags` list, default empty).
- `format_line` appends ` #tag` for each tag after the priority suffix.
- `list --tag X` filters to tasks with that tag (combines with `--sort`).
- Marked F06 passing.
- Next: F07 (due dates: `--due`, `due:` suffix after tags, `--overdue --today`).

## Session: F07 due dates
- `add TITLE --due YYYY-MM-DD` stored as `due`; invalid -> `Invalid date: <v>` exit 1 (`validate_date`).
- `format_line` appends ` due:YYYY-MM-DD` after tags.
- `list --overdue [--today DATE]` shows open tasks with due < today (today defaults to real date). Added `flags` support to `parse_options`.
- Marked F07 passing.
- Next: F08 (edit).

## Session: F08 edit
- `edit ID --title NEW TITLE...` (title words joined with spaces) replaces title, prints `Edited <id>`; unknown id -> `No such task: <id>` exit 1.
- Marked F08 passing.
- Next: F09 (search).

## Session: F09 search
- `search TEXT` prints task lines whose title contains TEXT (case-insensitive), id order; none -> `No matches`.
- Marked F09 passing.
- Next: F10 (export json/csv).

## Session: F10 export
- `export --format json|csv`: json array of {id,title,done,priority,tags,due}; csv with header, done true/false, tags joined by `;`, empty due. Empty store -> `[]`.
- Marked F10 passing.
- Next: F11 (stats), then F12 (undo; needs history snapshots recorded on add/done/delete/edit).

## Session: F11 stats
- Implemented `stats` (open/done/total counts, excluding deleted tasks). Marked F11 passing.
- Next: F12 undo (needs a history stack persisted in tasks.json, recording state snapshots before add/done/delete/edit; restore previous state incl. next_id).

## Session: F12 undo
- Added `record(state)` which pushes `{next_id, tasks}` snapshot onto `state["history"]`; called right before mutation in add, done, delete, edit (after validation, so failed commands aren't recorded).
- `undo` pops the last snapshot, restores tasks and next_id, prints `Undone`; empty history -> `Nothing to undo` exit 1.
- Marked F12 passing. All features F01-F12 implemented; next: nothing (spec complete).
