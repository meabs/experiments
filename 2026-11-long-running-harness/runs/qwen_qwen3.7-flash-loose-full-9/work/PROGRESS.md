# Progress

## Session 1
- Implemented `tasks.py` with basic structure (load/save tasks, undo history)
- Implemented F01: **add** command - creates open tasks with auto-incrementing IDs
- Written tests for F01 in `tests/test_f01_add.py`
- F01 marked as passing in `feature_list.json`

## Session 2
- Implemented F02: **list** command - prints task lines in id order, "No tasks" when empty
- Written tests for F02 in `tests/test_f02_list.py`
- F02 marked as passing in `feature_list.json`

## Session 3
- Implemented F03: **done** command - marks task as done, prints "Done <id>", error on unknown ID
- Written tests for F03 in `tests/test_f03_done.py`
- F03 marked as passing in `feature_list.json`

## Session 4
- Implemented F04: **delete** command - removes task, prints "Deleted <id>", never reuses deleted IDs
- Written tests for F04 in `tests/test_f04_delete.py`
- F04 marked as passing in `feature_list.json`

## Session 5
- Verified F05: **priority** feature (--priority high|medium|low, suffixes, list --sort priority)
- Written tests for F05 in `tests/test_f05_priority.py`
- F05 marked as passing in `feature_list.json`

## Session 6
- Verified F06: **tags** feature (--tag repeatable, list --tag filter)
- The implementation was already present in tasks.py from previous sessions
- Written tests for F06 in `tests/test_f06_tags.py` covering:
  - Adding tasks with single and multiple tags
  - Tag suffix order (priority before tags)
  - list --tag filtering
  - Tags stored correctly in tasks.json
- F06 marked as passing in `feature_list.json`

## Session 7
- Verified F07: **due dates** feature (--due YYYY-MM-DD, list --overdue --today DATE)
- Implementation was already present in tasks.py from previous sessions
- Written comprehensive tests in `tests/test_f07_due.py` covering:
  - Adding tasks with --due date
  - Due date suffix format in task lines (priority + tags + due)
  - Invalid date rejection (bad month, day, format, leap year edge cases)
  - list --overdue with and without --today
  - Overdue excludes done tasks and tasks without due dates
- F07 marked as passing in `feature_list.json`

## Next
- Implement F08: edit command
- Implement F09: search command
- Implement F10: export command
- Implement F11: stats command
- Implement F12: undo feature
