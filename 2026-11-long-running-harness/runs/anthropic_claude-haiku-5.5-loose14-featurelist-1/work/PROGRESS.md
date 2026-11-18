# Progress

## Session 1
- Created tasks.py skeleton: JSON storage (load/save, next_id), fail() helper, command dispatch table `COMMANDS`.
- Implemented F01 (add). Verified `add` prints Added 1 / Added 2 and writes tasks.json.
- feature_list.json: F01 set to passes=true.

## Next
- F02 (list) onward: add cmd_* functions to COMMANDS in priority order.

## Session 2
- Implemented F02 (list): task_line() helper + cmd_list; prints 'No tasks' when empty.
- Verified list output for empty and two-task cases.
- feature_list.json: F02 set to passes=true.

## Next
- F03 (done) onward.

## Session 3
- Implemented F03 (done): cmd_done in COMMANDS; prints 'Done <id>', unknown id -> 'No such task: <id>' exit 1.
- Verified done 2 / list / done 9 behaviour.
- feature_list.json: F03 set to passes=true.

## Next
- F04 (delete) onward.
