# Progress

## Implemented Features

All 12 features from SPEC.md are implemented in `tasks.py`:

1. **add** - Creates tasks with optional `--priority`, `--tag` (repeatable), `--due` flags
2. **list** - Lists all tasks; supports `--sort priority`, `--tag`, `--overdue --today` filters
3. **done** - Marks a task as done
4. **delete** - Removes a task
5. **priority** - Tasks display `(high)` or `(low)` suffix; `medium` has no suffix; `list --sort priority` orders high, medium, low
6. **tags** - Tasks display `#tag` suffixes; `list --tag X` filters by tag
7. **due dates** - Tasks display `due:YYYY-MM-DD` suffix; `list --overdue` shows past-due open tasks
8. **edit** - `edit ID --title NEW` replaces the title
9. **search** - Case-insensitive title search
10. **export** - JSON and CSV format export
11. **stats** - Prints open, done, total counts
12. **undo** - Reverts last mutating command (add/done/delete/edit); persists across runs via undo_history in tasks.json

## Error Handling
- Invalid priority → `Invalid priority: <value>` to stderr, exit 1
- Invalid date → `Invalid date: <value>` to stderr, exit 1
- Unknown task id for done/delete/edit → `No such task: <id>` to stderr, exit 1
- Nothing to undo → `Nothing to undo` to stderr, exit 1
- Unknown command → error to stderr, exit 1

## Next Steps
None - all spec requirements are complete.
