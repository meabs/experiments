# Progress

## Session 1
- Implemented F01 (`add`) in tasks.py: stores {"next_id", "tasks"} in tasks.json.
- Test: tests/test_add.py (passes).
- Note: init.sh smoke check still fails because `list` (F02) is not implemented yet.

## Next
- F02 (`list`), then F03 onward in priority order.

## Session 2
- Implemented F02 (`list`) with task_line() formatter (suffixes to be added in F05-F07).
- Tests: tests/test_list.py. init.sh smoke passes.

## Next
- F03 (`done`), then F04 onward in priority order.

## Session 3
- Implemented F03 (`done`) with find_task() helper; tests/test_done.py passes.
- init.sh passes.

## Next
- F04 (`delete`), then F05 onward in priority order.

## Session 4
- Implemented F04 (`delete`): removes task, prints `Deleted <id>`; ids never reused (next_id persists). Test: tests/test_delete.py.
- init.sh passes.

## Next
- F05 (priority: --priority, suffix, list --sort priority), then F06 onward in priority order.

## Session 5
- Implemented F05 (priority): `add --priority`, `(high)`/`(low)` suffix, `list --sort priority`, `Invalid priority` error. Test: tests/test_priority.py.
- init.sh passes.

## Next
- F06 (tags: --tag, #suffix, list --tag), then F07 onward in priority order.

## Session 6
- Implemented F06 (tags): `add --tag` (repeatable, stored as "tags" list), `#tag` suffix after priority, `list --tag X` filter (combinable with --sort). Test: tests/test_tags.py.
- init.sh passes.

## Next
- F07 (due dates: --due, due:, list --overdue --today), then F08 onward in priority order.
