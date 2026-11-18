# Progress

## Session 1
- Implemented F01 (`add`) in tasks.py. Storage: tasks.json = {"next_id", "tasks": [{id,title,done}]}.
- Test: tests/test_add.py (passes). F01 marked passing.
- init.sh smoke check still reports BROKEN because it runs `list` (F02, not yet implemented). Expected.
- Next: F02 (`list`), then F03 onward in order. Undo (F12) will likely need a history field
  added to tasks.json storage (snapshots before each mutation).

## Session 2
- Implemented F02 (`list`) with format_task helper; test in tests/test_list.py. F02 marked passing.
- Next: F03 (`done`), then F04 onward in order. Undo (F12) will need snapshot history.

## Session 3
- Implemented F03 (`done`) with test in tests/test_done.py. F03 marked passing.
- Next: F04 (`delete`; ids never reused, so next_id must stay stored), then F05 onward in order.

## Session 4
- Implemented F04 (`delete`) with ids never reused (next_id stored); test in tests/test_delete.py. F04 marked passing.
- Next: F05 (`priority`, incl. `list --sort priority`), then F06 onward in order.

## Session 5
- Implemented F05 (`--priority` on add, suffix for high/low, `list --sort priority`, invalid priority error) via a parse_options helper. Test: tests/test_priority.py. F05 marked passing.
- Next: F06 (tags: `--tag` repeatable on add, suffix `#a #b`, `list --tag` filter), then F07 onward in order.

## Session 6
- Implemented F06 (tags): repeatable `--tag` on add (stored as list), suffix ` #a #b` after priority, `list --tag X` filter. parse_options now collects REPEATABLE options. Test: tests/test_tags.py. F06 marked passing.
- Next: F07 (due dates, `--overdue --today`), then F08 onward in order.

## Session 7
- Implemented F07 (due dates): `add --due` with validation (`Invalid date: <v>`), `due:YYYY-MM-DD` suffix after tags, `list --overdue [--today DATE]` (open tasks with due < today). Test: tests/test_due.py. F07 marked passing.
- Next: F08 (edit --title), then F09 onward in order.

## Session 8
- Implemented F08 (`edit ID --title NEW TITLE`; title words joined by spaces). Test: tests/test_edit.py. F08 marked passing.
- Next: F09 (search), then F10 onward. Undo (F12) still needs snapshot history.

## Session 9
- Implemented F09 (`search TEXT`: case-insensitive title substring, id order, `No matches`). Test: tests/test_search.py. F09 marked passing.
- Next: F10 (export json/csv), then F11 (stats), then F12 (undo; needs snapshot history stored in the data file so it survives runs).

## Session 10
- Implemented F10 (`export --format json|csv`, fields per SPEC, ';' tags, empty due blank/null). Test: tests/test_export.py. F10 marked passing.
- Next: F11 (stats), then F12 (undo with snapshot history stored in data file).

## Session 11
- Implemented F11 (`stats`: open/done/total, deleted excluded). Test: tests/test_stats.py. F11 marked passing.
- Next: F12 (undo; snapshot history stored in data file so it survives runs; failed commands not recorded).

## Session 12
- Implemented F12 (`undo`): main() snapshots {next_id, tasks} before add/done/delete/edit and appends to `history` in tasks.json only if the command succeeds; `undo` pops and restores. Test: tests/test_undo.py. F12 marked passing.
- All features F01-F12 now passing. Spec complete.
