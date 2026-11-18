# Progress

## Session 1
- Implemented F01 (add): tasks.py with JSON storage (`next_id`, `tasks`), command dispatch, `add`.
- Test: tests/test_add.py (passes).
- init.sh smoke check still reports BROKEN only because `list` (F02) is not implemented yet.
- Next: F02 (list), then F03 onward in order.

## Session (F12 undo)
- Implemented F12: tasks.json now has a `history` list of pre-mutation snapshots
  (`next_id`, `tasks`). `main` records a snapshot only after add/done/delete/edit succeed
  (failed commands exit before recording). `undo` pops the last snapshot and restores it.
- Test: tests/test_undo.py (5 tests). All 26 tests pass; init.sh smoke OK.
- All features F01-F12 now pass. Next: nothing outstanding.
