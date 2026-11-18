# PROGRESS

## Session 1
- Implemented F01 (add): tasks.py with JSON storage (`{"next_id", "tasks"}`), `cmd_add`, command dispatch table `COMMANDS`.
- Test: tests/test_add.py (passing).
- init.sh smoke step still reports BROKEN because it runs `list`, which is F02 (not yet implemented). Expected until F02.

## Next
- F02: list command (add to COMMANDS table in tasks.py, test in tests/).

## Session 2
- Implemented F02 (list): `cmd_list`, `task_line` helper (base line format), registered in COMMANDS.
- Test: tests/test_list.py (passing). init.sh smoke now ok.
- feature_list.json: F02 set to passes true.

## Next
- F03: done command (use task_line; unknown id -> 'No such task: <id>').

## Session 3
- Implemented F03 (done): `find_task`, `parse_id`, `cmd_done` registered in COMMANDS.
- Test: tests/test_done.py (passing). feature_list.json F03 set to passes true.

## Next
- F04: delete command (remove task, ids never reused via next_id; unknown id -> 'No such task').

## Session 4
- Implemented F04 (delete): `cmd_delete` registered in COMMANDS; ids not reused (next_id untouched).
- Test: tests/test_delete.py (passing). F04 set to passes true.

## Next
- F05: priority (--priority on add, suffix, list --sort priority). Note: add currently only takes args[0]; parse options.

## Session 5
- Implemented F05 (priority): `parse_opts` helper for option parsing, `--priority` on add (default medium, suffix for high/low), `list --sort priority`.
- Test: tests/test_priority.py (passing). F05 set to passes true.

## Next
- F06: tags (--tag repeatable on add, '#work #home' suffix after priority, list --tag filter). Use parse_opts with ("priority","tag") style value opts; tags stored as list in task["tags"].

## Session 6
- Implemented F06 (tags): `--tag` repeatable on add (stored as task["tags"]), `#a #b` suffix after priority, `list --tag` filter (task must have all given tags). Test: tests/test_tags.py. F06 set to passes true.

## Next
- F07: due dates (--due on add, `due:YYYY-MM-DD` suffix, invalid date error, list --overdue --today).
