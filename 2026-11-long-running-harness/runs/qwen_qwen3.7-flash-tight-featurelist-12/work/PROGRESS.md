# Progress

## Session 1
- Implemented F01 (add): `python3 tasks.py add TITLE` creates a task with sequential ID, prints "Added <id>", persists to tasks.json
- Next: F02 (list)

## Session 2
- Implemented F02 (list): `python3 tasks.py list` prints one task line per task in id order, or "No tasks" when empty
- Task line format: `<id> [ ] <title>` for open, `<id> [x] <title>` for done
- Added `task_line()` helper function for formatting
- Next: F03 (done)

## Session 3
- Implemented F03 (done): `python3 tasks.py done ID` marks task as done, prints "Done <id>"
- Unknown ID prints "No such task: <id>" to stderr and exits 1
- Next: F04 (delete)
