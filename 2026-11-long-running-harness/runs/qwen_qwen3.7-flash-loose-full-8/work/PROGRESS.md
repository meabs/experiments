# Progress

## Session 1
- Created tasks.py with basic structure and F01 (add) implemented
- Created tests/test_f01_add.py with 4 tests for the add command
- Fixed title storage issue (nargs="+" returns list, need to join)
- Committed work after F01 passes all tests

## Session 2
- Verified F02 (list) implementation works correctly
- All 3 F02 tests pass (empty list, two adds, id ordering)
- Marked F02 as passing in feature_list.json
- Committed after verification

### Next up: F03 (done)

## Session 3
- Created tests/test_f03_done.py with 4 tests for the done command
- All F03 tests pass (marks task done, shows [x], unknown id error, double done)
- Marked F03 as passing in feature_list.json
- Committed after verification

### Next up: F04 (delete)

## Session 4
- Created tests/test_f04_delete.py with 5 tests for the delete command
- All F04 tests pass (prints id, removes task, unknown id error, preserves next_id, deletes done task)
- Marked F04 as passing in feature_list.json
- Committed after verification

### Next up: F05 (priority)

## Session 5
- Fixed F05 (priority): removed `choices` from argparse `--priority` argument so that invalid values produce exit code 1 with message "Invalid priority: <value>" instead of argparse's default exit code 2
- Created tests/test_f05_priority.py with 7 tests covering: high/medium/low suffixes, default medium, sort by priority, invalid priority error, JSON storage
- All F05 tests pass
- Marked F05 as passing in feature_list.json
- Committed after verification

### Next up: F06 (tags)

