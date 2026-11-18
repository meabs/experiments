# PROGRESS

## Session 1
- Implemented F01 (add) in tasks.py: store is `tasks.json` = `{"next_id": N, "tasks": [{id,title,done}]}`,
  atomic save via temp file + os.replace. argparse-based parser; usage errors exit 1; TaskError -> stderr, exit 1.
- Added tests/test_f01_add.py (passing).
- init.sh smoke check still reports BROKEN because it runs `list` (F02, not yet implemented). Expected.
- Next: F02 (list).

## Session 2
- Implemented F02 (list) in tasks.py: `format_task` helper (line format, to be extended with suffixes)
  and `cmd_list` (id order, 'No tasks' when empty).
- Added tests/test_f02_list.py (passing). init.sh smoke passes.
- Next: F03 (done).

## Session 3
- Implemented F03 (done) in tasks.py: `cmd_done` + `done ID` subparser; unknown id -> 'No such task: <id>', exit 1.
- Added tests/test_f03_done.py (passing). init.sh passes.
- Next: F04 (delete).

## Session: F04 (delete)
- Added `delete ID` command (prints `Deleted <id>`, unknown id -> error). Ids never reused (next_id stored separately).
- Test: tests/test_f04_delete.py. init.sh passes.
- Next: F05 (priority).

## Session: F05 (priority)
- Added --priority (high|medium|low, default medium) to add; invalid -> "Invalid priority: <v>" exit 1.
- Line suffix " (high)"/" (low)"; medium has no suffix. Old tasks without priority treated as medium.
- list --sort id|priority (priority: high, medium, low; ties by id).
- Tests: tests/test_f05_priority.py. init.sh passes. F05 marked passing.
- Next: F06 (tags).

## Session: F06 (tags)
- add --tag (repeatable, stored as "tags" list); line suffix " #a #b" after priority; list --tag NAME filters.
- Old tasks without "tags" treated as no tags. Tests: tests/test_f06_tags.py. init.sh passes. F06 marked passing.
- Next: F07 (due dates).
