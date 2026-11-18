# Progress

## Session 1
- Implemented F01 (add): `add TITLE` creates an open task, prints `Added <id>`, persists to tasks.json

## Session 2
- Implemented F02 (list): `list` prints tasks in id order or "No tasks"
- Extended add with --priority, --tag, --due options for future features
- Added task_line() helper for formatted output

## Session 3
- Implemented F03 (done): `done ID` marks a task done, prints 'Done <id>', unknown id prints error to stderr and exits 1
- Added undo history tracking for done operations
- Verified: done 2 works, list shows [x], done 9 errors correctly

## Next: F04 (delete) - delete ID removes the task, prints 'Deleted <id>', ids are never reused, unknown id error
