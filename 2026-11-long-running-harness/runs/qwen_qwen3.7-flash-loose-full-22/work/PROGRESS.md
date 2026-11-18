# Progress

## Session 1
- Implemented F01 (add command) - all tests pass
- Created tasks.py with basic structure for all commands
- Created tests/test_f01_add.py with tests for add

## Session 2
- Fixed JSON key type mismatch bug (integer vs string keys)
- All existing tests pass (F01, F02)
- Next: Implement F03 (done command)

## Session 3
- Fix JSON key type mismatch - resolved the root cause of test failures
- All tests now pass including F02 list tests
- Updated feature_list.json: F02 passes = true
- Next: Implement F03 (done command)

## Session 4
- F03 (done command) was already implemented in tasks.py
- Verified all F03 tests pass
- Marked F03 as passing in feature_list.json
- Next: Implement F04 (delete command)

## Session 5
- F07 (due dates) was already implemented in tasks.py
- Created tests/test_f07_due_dates.py with 6 tests covering:
  - Adding tasks with --due shows due:YYYY-MM-DD suffix
  - Invalid date exits 1 with proper error message
  - --overdue shows only OPEN tasks due before --today
  - Suffix order: priority, tags, then due date
  - Tasks without --due have no due suffix
- Marked F07 as passing in feature_list.json
- Next: Implement F08 (edit command)

## Session 6
- F08 (edit command) was already implemented in tasks.py
- Created tests/test_f08_edit.py with 6 tests covering:
  - edit prints 'Edited <id>'
  - list shows updated title after editing
  - unknown id exits 1 with proper error message
  - editing preserves priority, tags, due date
  - can edit done tasks
  - missing --title flag is an error
- Marked F08 as passing in feature_list.json
- Next: Implement F09 (search command)
