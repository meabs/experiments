# Progress

## Session 1
- Implemented F01 (add) in tasks.py, plus a basic `list` (F02 partly; its test already passes but F02 is not yet marked).
- Storage: tasks.json = {"next_id": int, "tasks": [{id,title,done}]}. Extend this shape for priority/tags/due/history.
- Tests in tests/test_add.py (run: python3 -m unittest discover -s tests).
- Next: F02 (mark passing after verifying), then F03 done, F04 delete, F05 priority, F06 tags, F07 due dates, F08 edit, F09 search, F10 export, F11 stats, F12 undo (needs a history list in tasks.json).

## Session 2
- Verified F02 (list): tests test_list_empty and test_list_after_adds pass. Marked F02 passes=true.
- Next: F03 (done command), then F04 delete, F05 priority, F06 tags, F07 due, F08 edit, F09 search, F10 export, F11 stats, F12 undo.

## Session 3
- Implemented F03 (done): cmd_done in tasks.py; tests in tests/test_done.py (pass). Marked F03 passes=true.
- Next: F04 delete (ids never reused via next_id), then F05 priority, F06 tags, F07 due, F08 edit, F09 search, F10 export, F11 stats, F12 undo.

## Session: F04 (delete)
- Added `delete ID` command (removes task, prints `Deleted <id>`, unknown id -> `No such task`). Ids never reused (next_id persisted).
- Tests: tests/test_delete.py. All tests + init.sh pass.
- Next: F05 priority (add --priority, suffix, list --sort priority).

## Session: F05 (priority)
- `add` now parses options via `parse_opts`; `--priority high|medium|low` stored per task (default medium), invalid -> `Invalid priority: <v>`.
- `list` shows `(high)`/`(low)` suffix; `list --sort priority` orders high/medium/low, ties by id.
- Tests: tests/test_priority.py. All tests + init.sh pass.
- Next: F06 tags (--tag repeatable, `#work #home` suffix after priority, `list --tag`).

## Session: F06 (tags)
- `add --tag` repeatable, stored as `tags` list; line suffix ` #work #home` after priority; `list --tag X` filters.
- Tests: tests/test_tags.py. All tests + init.sh pass.
- Next: F07 due dates (--due, due:YYYY-MM-DD suffix, list --overdue --today).

## Session: F07 (due dates)
- `add --due YYYY-MM-DD` validated (`Invalid date: <v>`), stored as `due`; line suffix ` due:DATE` after tags.
- `list --overdue [--today DATE]` shows open tasks with due < today (default real date).
- parse_opts now supports boolean flags (value "flag").
- Tests: tests/test_due.py. All tests + init.sh pass.
- Next: F08 edit (--title replaces title, 'Edited <id>').

## Session: F08 (edit)
- `edit ID --title NEW TITLE` (title = all words after --title joined by space); prints `Edited <id>`; unknown -> `No such task`.
- Tests: tests/test_edit.py. All tests + init.sh pass.
- Next: F09 search.

## Session: F09 (search)
- `search TEXT` (case-insensitive substring on title, id order, `No matches` when none).
- Tests: tests/test_search.py. All tests + init.sh pass.
- Next: F10 export (json/csv).

## Session: F10 (export)
- `export --format json|csv` implemented (json array with id/title/done/priority/tags/due; csv header + rows, tags joined by `;`).
- Tests: tests/test_export.py. All tests + init.sh pass. F10 marked passing.
- Next: F11 stats.

## Session: F11 (stats)
- `stats` prints `open: N`, `done: N`, `total: N` (deleted tasks are gone from the store, so excluded).
- Tests: tests/test_stats.py. All tests + init.sh pass. F11 marked passing.
- Next: F12 undo (history of mutating commands stored in tasks.json, restores prior state incl. next_id).

## Session: F12 (undo)
- Undo history stored in tasks.json as `history`: each successful add/done/delete/edit pushes a snapshot `{next_id, tasks}` (via `record()`) before mutating. `undo` pops and restores it, prints `Undone`; empty -> `Nothing to undo` (exit 1).
- Tests: tests/test_undo.py. All 32 tests + init.sh pass. F12 marked passing.
- All features F01-F12 now pass. Next: nothing required; spec is complete.
