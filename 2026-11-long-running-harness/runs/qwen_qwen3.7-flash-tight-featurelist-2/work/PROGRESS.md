# Progress

## Session 1
- Implemented F01 (add): `add TITLE` creates a task, prints `Added <id>`
- Basic infrastructure: tasks.json storage, load/save functions, undo history structure

## Session 2
- Implemented F02 (list): `list` prints tasks in id order, or "No tasks" when empty
- Enhanced print_task to support priority, tags, and due date suffixes (prep work for later features)
- Updated feature_list.json: F01=true, F02=true

## Session 3
- Implemented F03 (done): `done ID` marks task done, prints `Done <id>`, handles unknown ids with stderr error and exit 1
- Added undo support for done command (saves snapshot before mutation)
- Also added stub implementations for remaining commands (delete, edit, search, export, stats, undo)
- Updated feature_list.json: F03=true

## Session 4
- Verified F04 (delete) was already implemented in Session 3 stub. Full testing confirms:
  - `delete ID` removes the task and prints `Deleted <id>`
  - IDs are never reused (next add gets incremented id)
  - Unknown id gives `No such task: <id>` on stderr with exit 1
  - Undo works correctly for delete (restores task and next_id)
- Updated feature_list.json: F04=true

## Next
- F05 (priority) - add --priority high|medium|low, suffix '(high)'/'(low)', list --sort priority


