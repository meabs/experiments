# Progress

## Session 1: F01 (add + list) - DONE
- Implemented `tasks.py` with basic add and list commands
- Data stored in `tasks.json` with proper JSON structure
- Tasks have id, title, done fields
- Next ID tracking works correctly
- "No tasks" message when empty store

## Session 2: F03 (done command) - DONE
- Implemented `done ID` command
- Marks task as done, prints 'Done <id>'
- Handles unknown IDs with error

## Session 3: F04 (delete command) - DONE
- Implemented `delete ID` command
- Removes task from store, prints 'Deleted <id>'
- Unknown IDs print 'No such task: <id>' to stderr, exit 1
- Made save_tasks robust to include 'id' field in each task
- Fixed load_tasks to handle tasks missing 'id' key

## Session 4: F05 (priority feature) - DONE
- Added --priority high|medium|low flag to add command (default medium)
- Display priority suffix in task lines: '(high)' or '(low)', no suffix for medium
- Support 'list --sort priority' ordering: high, medium, low, ties by id
- Invalid priority values produce error: 'Invalid priority: <value>'
- Refactored task_line() helper for consistent display format with extensible suffixes

## Next: F06 (tags feature)
- Need to implement --tag repeatable flag on add
- Task line suffixes: #tag1 #tag2 (after priority suffix)
- list --tag work filters tasks with that tag
