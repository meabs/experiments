# Progress

## Completed
- Implemented all 12 features from SPEC.md in tasks.py:
  - **add**: Creates tasks with optional --priority, --tag, --due flags
  - **list**: Lists tasks with --sort priority, --tag filter, --overdue/--today options
  - **done**: Marks tasks as done
  - **delete**: Removes tasks
  - **priority**: High/medium/low priorities (default medium), sorting support
  - **tags**: Repeatable --tag flags, filtering by tag
  - **due dates**: YYYY-MM-DD format validation, overdue detection
  - **edit**: Updates task titles
  - **search**: Case-insensitive title search
  - **export**: JSON and CSV export formats
  - **stats**: Open/done/total counts
  - **undo**: Persistent undo history across runs (stored in tasks.json)
- All error cases handled properly (invalid IDs, invalid dates, invalid priorities, etc.)
- Data persisted in tasks.json in current working directory
- Task IDs are integers starting at 1, never reused after deletion

## Verified
- All commands tested end-to-end including edge cases:
  - `list` with no tasks prints "No tasks"
  - `search` with no matches prints "No matches"
  - Invalid task IDs for done/delete/edit print "No such task: <id>"
  - Invalid priority values print "Invalid priority: <value>"
  - Invalid date values print "Invalid date: <value>"
  - Undo works multiple times and prints "Nothing to undo" when empty
  - Priority sorting orders high→medium→low, ties by id
  - Overdue filter correctly identifies open tasks past due date

## Next steps
None - implementation is complete.
