# Progress

## Session 1
- Done F01 (add): tasks.py with JSON store (tasks.json: {next_id, tasks[]}), `add TITLE`
  prints `Added <id>`. Test: tests/test_add.py.
- init.sh smoke check still reports BROKEN because it runs `list`, which is F02 (not yet implemented).
- Next: F02 (list), then F03 onward in order. Add-only storage has no priority/tags/due yet; extend
  the task dict in later features. Undo (F12) will need a history snapshot in the state file.

## Session 2
- Done F02 (list): `list` prints `<id> [ ] title` / `[x]` in id order, or `No tasks`. Test: tests/test_list.py.
- init.sh smoke check passes now.
- Next: F03 (done), then F04 onward in order.

## Session 3
- Done F03 (done): `done ID` marks task done, prints `Done <id>`; unknown id -> `No such task: <id>` exit 1.
  Test: tests/test_done.py. init.sh passes.
- Next: F04 (delete), then F05 onward in order.

## Session 4
- Done F04 (delete): `delete ID` removes task, prints `Deleted <id>`; ids not reused (next_id persists);
  unknown id -> `No such task: <id>` exit 1. Test: tests/test_delete.py.
- Next: F05 (priority), then F06 onward in order.

## Session 5
- Done F05 (priority): `add --priority high|medium|low` (default medium, stored in task dict as
  `priority`), suffix `(high)`/`(low)`, `list --sort priority`, invalid -> `Invalid priority: <v>`.
  Added `parse_opts(args, names)` helper for `--name value` options (repeatable). Test: tests/test_priority.py.
- Next: F06 (tags), then F07 onward in order.

## Session 6
- Done F06 (tags): `add --tag X` repeatable (stored as `tags` list), suffix ` #work #home` after
  priority, `list --tag X` filters. Test: tests/test_tags.py.
- Next: F07 (due dates), then F08 onward in order.
