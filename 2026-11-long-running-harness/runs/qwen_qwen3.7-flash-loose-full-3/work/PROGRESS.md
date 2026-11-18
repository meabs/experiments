# Progress Log

## Session 1
- Fixed bug in test_f01_add.py: `run_tasks` function referenced `self.tmpdir` which was not available (it's a standalone function, not a method). Fixed by using absolute path to tasks.py.
- Implemented tests for F01 (add command): 4 tests covering add with ID output, sequential IDs, tasks.json creation, and task state verification.
- All F01 tests pass. Marked F01 as passing in feature_list.json.
- Next: Work on F02 (list command).

## Session 2
- F02 (list) tests already existed from session 1 and all pass. Marked F02 as passing.
- Implemented tests for F03 (done command): 5 tests covering done output, list shows [x], unknown id error, nonexistent id error, multiple tasks only marks target.
- All 13 tests pass. Marked F03 as passing.
- Next: Work on F04 (delete command).

## Session 3
- F04 (delete) implementation already exists and works. Implemented 5 tests covering delete output, removal from list, id reuse prevention, unknown id error, nonexistent id error.
- All 18 tests pass. Marked F04 as passing.
- Next: Work on F05 (priority).

## Session 4
- F05 (priority) implementation already exists and works. All 6 tests pass covering high/low/medium suffixes, default priority, sort priority ordering, and invalid priority error.
- Marked F05 as passing in feature_list.json.
- Next: Work on F06 (tags).

## Session 5
- F06 (tags) implementation already exists and works. Implemented 6 tests covering single tag, multiple tags in order, tag filter matching/excluding, priority-then-tags suffix order, and no-tags case.
- All 30 tests pass. Marked F06 as passing in feature_list.json.
- Next: Work on F07 (due dates).

## Session 6
- F07 (due dates) implementation already exists and works. Implemented 6 tests covering due date suffix in list output, priority+tags+due combined suffix order, invalid date rejection (both bad values and bad format), overdue filtering showing only open past-due tasks, and no-due task having no suffix.
- All 36 tests pass. Marked F07 as passing in feature_list.json.
- Next: Work on F08 (edit command).
