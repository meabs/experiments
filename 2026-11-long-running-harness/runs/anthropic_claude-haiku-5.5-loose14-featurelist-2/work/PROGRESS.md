# PROGRESS

## Session 1
- Created tasks.py with storage helpers (tasks.json: {"next_id", "tasks"}), error helper, command dispatch.
- Implemented F01 (add): prints `Added <id>`, ids start at 1 and increment, creates tasks.json.
- Verified manually in a temp dir. F01 marked passing.

## Next
- F02 (list), then F03 onward in priority order. Extend `tasks` entries with priority/tags/due later.

## Session 2
- Implemented F02 (list): `format_task` helper prints `<id> [ ] <title>` / `[x]`, `No tasks` when empty, id order.
- Verified in a temp dir. F02 marked passing.

## Next
- F03 (done), then F04 onward in priority order. Use `format_task` as the base for suffixes (F05+).

## Session 3
- Implemented F03 (done): `cmd_done` marks task done, prints `Done <id>`; unknown id -> `No such task: <id>` exit 1.
- Verified in a temp dir. F03 marked passing.

## Next
- F04 (delete), then F05 onward in priority order. Note: ids must never be reused (keep next_id in store).

## Session 4
- Implemented F04 (delete): `cmd_delete` removes task, prints `Deleted <id>`; unknown id -> `No such task: <id>` exit 1. next_id is kept, so ids are not reused.
- Verified in a temp dir. F04 marked passing.

## Next
- F05 (priority), then F06 onward in priority order.

## Session 5
- Implemented F05 (priority): `add --priority high|medium|low` (stored per task, default medium), suffix `(high)`/`(low)` in `format_task`, `list --sort priority` (stable, ties by id), `Invalid priority: <v>` error. Added `parse_opts` helper for `--opt value` parsing.
- Verified in a temp dir. F05 marked passing.

## Next
- F06 (tags), then F07 onward in priority order. Tags suffix goes after priority in `format_task`.

## Session 6
- Implemented F06 (tags): `add --tag X` repeatable (stored as `tags` list, default empty), suffix ` #work #home` after priority in `format_task`, `list --tag X` shows tasks having all given tags.
- Verified in a temp dir. F06 marked passing.

## Next
- F07 (due dates), then F08 onward in priority order. Due suffix goes after tags in `format_task`.

## Session 7
- Implemented F07 (due dates): `add --due YYYY-MM-DD` (validated, `Invalid date: <v>`), stored as `due` (null when unset), suffix ` due:<date>` after tags, `list --overdue [--today DATE]` shows open tasks with due < today (default: real date).
- Verified in a temp dir. F07 marked passing.

## Next
- F08 (edit), then F09 onward in priority order. Add `edit` to COMMANDS.

## Session 8
- Implemented F08 (edit): `cmd_edit` replaces title (`--title` consumes all following words, since unquoted shell args split); `Edited <id>`; unknown id -> `No such task: <id>`. Registered in COMMANDS.
- Verified in a temp dir. F08 marked passing.

## Next
- F09 (search), then F10 onward in priority order. Note: F12 (undo) must snapshot state before mutating commands (add/done/delete/edit).

## Session 9
- Implemented F09 (search): `cmd_search` case-insensitive substring on title, id order, `No matches` when empty. Registered in COMMANDS.
- Verified in a temp dir. F09 marked passing.

## Next
- F10 (export: json/csv), then F11 (stats), F12 (undo; snapshot state before add/done/delete/edit).

## Session 10
- Implemented F10 (export): `export --format json|csv` (default json). JSON array with id,title,done,priority,tags,due (null when unset); CSV header + rows, tags joined by `;`. Empty store -> `[]` / header only.
- Verified in a temp dir. F10 marked passing.

## Next
- F11 (stats), then F12 (undo; snapshot state before add/done/delete/edit).

## Session 11
- Implemented F11 (stats): `cmd_stats` prints `open: N`, `done: N`, `total: N`; registered in COMMANDS.
- Verified in a temp dir (fresh store zeros; deleted tasks excluded). F11 marked passing.

## Next
- F12 (undo; snapshot state before add/done/delete/edit, persist history in tasks.json or sidecar, restore next_id).

## Session 12
- Implemented F12 (undo): before add/done/delete/edit, main snapshots `next_id` and `tasks`; after the command succeeds (failures exit via SystemExit and are not recorded) the snapshot is appended to `history` in tasks.json. `undo` pops it and restores state; `Undone`, or `Nothing to undo` (exit 1).
- Verified in a temp dir: undo of add reuses id, undo through done/edit/delete, failed commands not recorded, history persists across runs.
- All features F01-F12 now pass. Nothing left to do.
