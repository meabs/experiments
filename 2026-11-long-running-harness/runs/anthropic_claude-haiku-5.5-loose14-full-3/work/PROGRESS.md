# PROGRESS

## Session 1
- Done: F01 (add). tasks.py has JSON store (tasks.json: next_id, tasks[]), command dispatch, `add`.
- Test: tests/test_add.py passes.
- init.sh smoke currently BROKEN only because `list` (F02) is not implemented yet — expected.
- Next: F02 (list), then F03 onward in order.

## Session 2
- Done: F02 (list). Added cmd_list and format_task; tests/test_list.py passes; init.sh smoke ok.
- Next: F03 (done), then F04 onward in order.

## Session 3
- Done: F03 (done). Added cmd_done; tests/test_done.py passes; init.sh ok.
- Next: F04 (delete), then F05 onward in order.

## Session: F04 (delete)
- Added cmd_delete (ids never reused since next_id is persisted). Tests in tests/test_delete.py.
- F04 marked passing.
- Next: F05 (priority) onward in order (F05 priority, F06 tags, F07 due, F08 edit, F09 search, F10 export, F11 stats, F12 undo).

## Session: F05 (priority)
- add accepts --priority high|medium|low (default medium, stored in task); suffix '(high)'/'(low)'.
- list --sort priority orders high, medium, low, ties by id. Invalid -> 'Invalid priority: X'.
- tests/test_priority.py passes. F05 marked passing.
- Next: F06 (tags) onward in order. Note: add parses options in a loop; extend it for --tag/--due.

## Session: F06 (tags)
- add accepts repeatable --tag (stored as task "tags"); suffix ' #tag ...' after priority.
- list --tag TAG filters. tests/test_tags.py passes. F06 marked passing.
- Next: F07 (due dates) onward: F07 due, F08 edit, F09 search, F10 export, F11 stats, F12 undo.

## Session: F07 (due dates)
- add accepts --due YYYY-MM-DD (validated, 'Invalid date: X'); stored as task "due"; suffix ' due:DATE' after tags.
- list --overdue [--today DATE] shows open tasks with due < today (default: real date).
- tests/test_due.py passes. F07 marked passing.
- Next: F08 (edit) onward: F08 edit, F09 search, F10 export, F11 stats, F12 undo.

## Session: F08 (edit)
- Added cmd_edit (edit ID --title NEW TITLE; remaining args joined by space). tests/test_edit.py passes. F08 marked passing.
- Next: F09 (search), then F10 export, F11 stats, F12 undo.

## Session: F09 (search)
- Added cmd_search (case-insensitive substring on title, id order, 'No matches'). tests/test_search.py passes. F09 marked passing.
- Next: F10 (export) onward: F10 export, F11 stats, F12 undo.

## Session: F10 (export)
- Added cmd_export (--format json|csv) with exact fields; tests/test_export.py passes. F10 marked passing.
- Next: F11 (stats), then F12 (undo).

## Session: F11 (stats)
- Added cmd_stats (open/done/total lines). tests/test_stats.py passes. F11 marked passing.
- Next: F12 (undo): needs a history stack persisted in tasks.json, recording store snapshots before add/done/delete/edit.

## Session: F12 (undo)
- Each mutating command (add/done/delete/edit) snapshots {next_id, tasks} before change and
  pushes it to store["history"] (persisted in tasks.json) via save_mutation. cmd_undo pops and restores.
- Failed commands fail before saving, so they are not recorded. tests/test_undo.py passes (35 total). F12 marked passing.
- All features F01-F12 now pass. Next: nothing outstanding; spec complete.
