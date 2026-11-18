# PROGRESS

## Session 1
- Implemented F01 (`add`): tasks.py with JSON store (tasks.json, next_id, tasks list), argparse subcommand structure.
- tests/test_add.py covers F01; passes.
- init.sh smoke check still fails because it runs `list` (F02, not yet implemented) — expected.
- Next: F02 (`list`), then F03 onward in order.

## Session 2
- Implemented F02 (list): `list` prints task lines in id order, `No tasks` when empty.
  Added `task_line()` helper used for the `<id> [ ] <title>` format.
- Tests: tests/test_list.py. init.sh passes.
- Next: F03 (done). Then F04 delete, F05 priority, etc. (one feature per session).

## Session 3
- Implemented F03 (`done`): find_task helper, `done ID` prints `Done <id>`, unknown id -> stderr + exit 1.
- Tests: tests/test_done.py. init.sh passes.
- Next: F04 (delete), then F05 onward in order. Undo (F12) should record history for all mutating commands, so implement it last-ish and wrap save/mutations then.

## Session 4
- Implemented F04 (`delete`): removes task, prints `Deleted <id>`, unknown id -> stderr + exit 1. Ids never reused (next_id is kept).
- Tests: tests/test_delete.py. init.sh passes.
- Next: F05 (priority), then F06 onward in order. Undo (F12) still to do last.

## Session 5
- Implemented F05 (priority): `add --priority` (default medium, invalid -> `Invalid priority: <v>` exit 1), `(high)`/`(low)` suffix, `list --sort priority` (stable by id within ties).
- Tests: tests/test_priority.py. init.sh passes.
- Next: F06 (tags), then F07 onward in order. Undo (F12) still last.

## Session 6
- Implemented F06 (tags): `add --tag` (repeatable, stored as `tags` list), suffix ` #tag` after priority, `list --tag X` filter.
- Tests: tests/test_tags.py. init.sh passes.
- Next: F07 (due dates), then F08 onward in order. Undo (F12) still last.

## Session 7
- Implemented F07 (due dates): `add --due YYYY-MM-DD` (invalid -> `Invalid date: <v>` exit 1), suffix ` due:DATE` after tags, `list --overdue [--today DATE]` shows open tasks with due < today.
- Tests: tests/test_due.py. init.sh passes.
- Next: F08 (edit), then F09 onward in order. Undo (F12) still last.

## Session 8
- Implemented F08 (edit): `edit ID --title NEW TITLE` (title nargs="+", joined by spaces), prints `Edited <id>`, unknown id -> stderr + exit 1.
- Tests: tests/test_edit.py. init.sh passes.
- Next: F09 (search), then F10 onward in order. Undo (F12) still last.

## Session 9
- Implemented F09 (search): `search TEXT` case-insensitive substring on titles, `No matches` when empty.
- Tests: tests/test_search.py. init.sh passes.
- Next: F10 (export), then F11 stats, F12 undo last.

## Session 10
- Implemented F10 (export): `export --format json|csv`, fields id,title,done,priority,tags,due; csv tags joined by `;`.
- Tests: tests/test_export.py. init.sh passes.
- Next: F11 (stats), then F12 undo last.

## Session 11
- Implemented F11 (stats): prints `open: N`, `done: N`, `total: N`; deleted tasks excluded.
- Tests: tests/test_stats.py. init.sh passes.
- Next: F12 (undo), the last feature. Needs history recorded for add/done/delete/edit, restored with next_id.

## Session 12
- Implemented F12 (undo): each successful add/done/delete/edit pushes a snapshot of tasks+next_id onto `history` in tasks.json (persists across runs); `undo` pops and restores, prints `Undone`, or `Nothing to undo` (exit 1).
- Tests: tests/test_undo.py. init.sh passes. All features F01-F12 now passing.
- Next: nothing; spec complete.
