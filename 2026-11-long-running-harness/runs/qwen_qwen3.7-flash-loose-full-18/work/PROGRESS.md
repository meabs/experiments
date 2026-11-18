# Progress

## Session 1
- Fixed test infrastructure: `TasksTestBase.setUp()` now copies `tasks.py` to the temp directory
- Added tests for F02 (list): empty list, tasks in id order, done status shown
- Verified F01 (add) and F02 pass
- Marked F01 and F02 as passing in feature_list.json

## Session 2
- Fixed critical deepcopy bug: replaced `list(data['tasks'])` with `copy.deepcopy(data['tasks'])` 
  in all mutating commands (cmd_add, cmd_done, cmd_delete, cmd_edit) so undo history correctly
  captures task state before mutation
- Added test_f03_done.py with tests for done marking, list showing done status, and unknown id error
- Marked F03 as passing in feature_list.json

## Session 3
- Implemented F04 (delete): fixed ID reuse issue by persisting `next_id` counter in data store
  - Added `next_id` field to data dict, initialized to 1 on fresh creation
  - Modified `next_id()` function to use persisted counter instead of computing max from tasks
  - Updated `cmd_add` to increment `next_id` after assigning new task id
  - Updated `cmd_delete` to save `next_id` in undo history for proper restoration
  - Updated `cmd_undo` to restore `next_id` when undoing add/delete operations
- All 13 tests pass
- Marked F04 as passing in feature_list.json

## Next
- Work on F05 (priority): --priority high|medium|low, suffix '(high)'/'(low)', list --sort priority, invalid -> error
