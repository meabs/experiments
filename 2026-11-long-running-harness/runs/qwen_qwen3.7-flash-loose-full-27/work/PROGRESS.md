# Progress

## Session 1

### Completed
- **F01 (add)**: Implemented `add TITLE` command. Creates tasks with unique integer IDs starting at 1. Prints "Added <id>". Supports `--priority`, `--tag`, and `--due` flags (for F05-F07).
- **F02 (list)**: Implemented `list` command. Prints tasks in id order as `<id> [ ] <title>` format. Prints "No tasks" when empty. Supports `--sort priority`, `--tag`, `--overdue`, and `--today` flags (for F05-F07).
- Created tests in `tests/test_f01_f02.py` (7 tests).
- Created initial `tasks.py` with all core commands.

### Session 2

### Completed
- **F04 (delete)**: Verified `delete ID` command works correctly. Added tests in `tests/test_f04.py` (6 tests):
  - delete prints 'Deleted <id>'
  - delete removes task from list
  - next add doesn't reuse deleted id
  - unknown id returns error exit 1
  - delete persists across runs
  - delete works with tasks that have priority
- Updated feature_list.json to mark F04 as passes: true

### Session 3

### Completed
- **F05 (priority)**: Verified priority feature works. Tests added in `tests/test_f05.py` (7 tests).
- Updated feature_list.json to mark F05 as passes: true

### Session 4

### Completed
- **F06 (tags)**: Tags feature already implemented in tasks.py. Added comprehensive tests in `tests/test_f06.py` (8 tests):
  - add with multiple tags shows suffix '#work #home'
  - list --tag filters by tag
  - suffix order: priority then tags
  - single tag, no tags, done task with tags
  - filter with no match prints 'No tasks'
  - multiple adds with different tags persist correctly
- Updated feature_list.json to mark F06 as passes: true

### Next
- **F07 (due dates)**: Implement --due YYYY-MM-DD flag for add, suffix display, invalid date error, list --overdue --today DATE.

## Session 5

### Completed
- **F07 (due dates)**: Due dates feature was already fully implemented in tasks.py. Added comprehensive tests in `tests/test_f07.py` (9 tests):
  - add with due date shows suffix 'due:YYYY-MM-DD' after priority and tags
  - invalid date (2026-13-40) exits 1 with 'Invalid date: 2026-13-40'
  - invalid date format ('not-a-date') also errors
  - --overdue shows only open tasks due before --today
  - --overdue with no matching tasks prints 'No tasks'
  - task without due date has no suffix
  - due date persists across separate runs
  - done tasks are not shown as overdue
  - --overdue without --today uses real date
- Updated feature_list.json to mark F07 as passes: true

### Next
- **F08 (edit)**: Implement `edit ID --title NEW TITLE` command to replace task title.

## Session 6

### Completed
- **F08 (edit)**: Edit feature already implemented in tasks.py. Added comprehensive tests in `tests/test_f08.py` (7 tests):
  - edit 1 --title New title prints 'Edited 1'
  - list shows the new title after edit
  - unknown id returns error exit 1 with 'No such task: <id>'
  - multi-word titles preserved correctly
  - state persists across separate runs
  - other attributes (done/priority/tags/due) preserved during edit
  - editing one task doesn't affect others
- Updated feature_list.json to mark F08 as passes: true

### Next
- **F09 (search)**: Implement `search TEXT` command for case-insensitive substring search on titles.
