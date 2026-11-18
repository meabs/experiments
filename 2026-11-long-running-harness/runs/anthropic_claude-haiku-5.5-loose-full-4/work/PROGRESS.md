# Progress

## Session 1
- Implemented F01 (add): `tasks.py` with JSON store (`tasks.json`, `next_id`, `tasks`), command dispatch, `add`.
- Test: `tests/test_f01_add.py` (passing).
- feature_list.json: F01 set to passes=true.
- init.sh smoke check still reports BROKEN only because `list` (F02) is not implemented yet.

## Next
- F02 (list), then F03 onward in order. Note: `add` currently only takes title; priority/tags/due (F05-F07) need extra option parsing in cmd_add.

## Session 2
- Implemented F02 (list): `format_task` helper (task line format, reusable for later suffixes) and `cmd_list` (id order, 'No tasks').
- Test: `tests/test_f02_list.py` (passing). feature_list.json F02 set to passes=true.
- init.sh smoke check passes.

## Next
- F03 (done), then F04 onward in order. Keep using `format_task` for line output; priority/tags/due suffixes go in it (F05-F07).

## Session 3
- Implemented F03 (done): `cmd_done` marks task done, prints `Done <id>`; unknown id -> `No such task: <id>` on stderr, exit 1.
- Test: `tests/test_f03_done.py` (passing). feature_list.json F03 set to passes=true.
- init.sh passes.

## Next
- F04 (delete), then F05 onward in order.

## Session: F04 (delete)
- Added `delete ID` (prints `Deleted <id>`, unknown id -> error). Ids never reused since next_id is persisted.
- Tests: tests/test_f04_delete.py. All tests pass.

## Next
- F05 (priority), then F06 onward in order.

## Session: F05 (priority)
- `add --priority high|medium|low` (default medium, stored on task; invalid -> `Invalid priority: <v>`).
- `format_task` appends `(high)`/`(low)` suffix; medium has none.
- `list --sort priority` orders by priority then id. Added `parse_options(args, valued)` helper for option parsing (reuse for --tag, --due, --overdue, --today, --format, --title).
- Test: tests/test_f05_priority.py (passing). feature_list.json F05 passes=true.

## Next
- F06 (tags), then F07 onward in order.

## Session: F06 tags
- Added repeatable `--tag` to add (stored as `tags` list), `#tag` suffix after priority, `list --tag X` filter.
- Tests: tests/test_f06_tags.py. init.sh passes.
- Next: F07 due dates (--due, due:, --overdue --today).
