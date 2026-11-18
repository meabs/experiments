# Progress

## Session 1
- Fixed critical bug: JSON stores integer keys as strings, causing `done` command to fail on existing tasks. Added key conversion in `load_tasks()`.
- Implemented F02 (list): list prints one line per task in id order, or "No tasks" when empty. Shows `[ ]` for open and `[x]` for done tasks.
- Created tests/test_f02_list.py with 4 test cases.
- Marked F02 as passing in feature_list.json.

## Session 2
- Implemented F03 (done): done ID marks task done, prints "Done <id>", handles unknown IDs with error.
- Created tests/test_f03_done.py with 5 test cases.
- Marked F03 as passing in feature_list.json.

## Next
- Work on F04 (delete): delete ID removes task, prints "Deleted <id>"; ids never reused.
