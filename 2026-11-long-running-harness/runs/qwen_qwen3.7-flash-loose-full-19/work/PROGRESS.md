# Progress

## Session 1: Implemented F01 (add)

- Created `tasks.py` with full implementation skeleton including all commands
- Implemented `add` command: creates open tasks, prints "Added <id>"
- Task IDs are integers starting at 1, never reused after delete  
- Data stored in `tasks.json` in the current working directory
- Added `tests/test_f01_add.py` with tests for add functionality
- Marked F01 as passing in feature_list.json
- Committed with descriptive message

## Next: F02 (list) - list prints one line per task in id order, or 'No tasks'

## Session 2: Implemented F02 (list)

- Verified that `list` command works correctly: prints one line per task in id order
- Empty list prints "No tasks"
- Tasks display format: `<id> [ ] <title>` for open tasks, `<id> [x] <title>` for done tasks
- Added `tests/test_f02_list.py` with tests for list functionality
- Marked F02 as passing in feature_list.json
- Committed with descriptive message

## Next: F03 (done) - marks task done, prints 'Done <id>'; unknown id -> stderr error

