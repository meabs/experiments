# Progress Log

## Session 1 - F01 (add)
- Implemented basic tasks.py with core infrastructure
- Feature F01 (add): `add TITLE` creates an open task, prints "Added <id>"
  - Task IDs start at 1, increment sequentially
  - Data stored in tasks.json in current working directory
  - Undo history recorded for each mutation
- Created tests/test_f01_add.py with 4 unit tests
- All tests pass, smoke test passes

## Session 2 - F02 (list) + full rewrite
- Rewrote tasks.py with all commands implemented from scratch
- Fixed add command to properly save data via record_undo
- Feature F02 (list): `list` prints all tasks in id order, or "No tasks"
  - Supports `--sort priority`, `--tag TAG`, `--overdue --today DATE`
  - Done tasks show `[x]` marker
- All existing tests pass, smoke test passes

## Session 3 - F03 (done)
- Feature F03 (done): `done ID` marks task done, prints "Done <id>"
  - Unknown id exits 1 with "No such task: <id>"
  - list shows [x] marker for done tasks
- Created tests/test_f03_done.py with 3 unit tests
- All tests pass, smoke test passes

## Session 4 - F04 (delete)
- Feature F04 (delete): `delete ID` removes the task, prints "Deleted <id>"
  - Unknown id exits 1 with "No such task: <id>"
  - Deleted IDs are never reused (next_id preserved)
- Created tests/test_f04_delete.py with 5 unit tests
- All tests pass, smoke test passes

## Next
- Feature F05 (priority): --priority high|medium|low, suffix '(high)'/'(low)', list --sort priority
