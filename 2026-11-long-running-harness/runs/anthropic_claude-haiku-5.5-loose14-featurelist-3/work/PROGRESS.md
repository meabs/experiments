# PROGRESS

- F01–F10: implemented in earlier sessions (add, list, done, delete, priority, tags, due, edit, search, export).
- F11 (this session): added `stats` command (open/done/total counts, excluding deleted tasks). Verified manually.
- Next: F12 undo. Plan: store a `history` list in tasks.json of pre-mutation snapshots ({next_id, tasks}); push on successful add/done/delete/edit only; `undo` pops and restores, prints `Undone`, or fails with `Nothing to undo`.
- F12 (this session): undo implemented. Each successful add/done/delete/edit pushes a `{next_id, tasks}` snapshot onto `history` in tasks.json (via `snapshot`/`record`); `undo` pops and restores it, prints `Undone`, or fails with `Nothing to undo`. Verified: undo after add reuses id, repeated undo through done/edit/delete, failed commands not recorded, history persists across runs.
- All features F01–F12 now pass. Next: nothing outstanding.
