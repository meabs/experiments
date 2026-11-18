# Progress

## Implemented Features

All 12 features from SPEC.md are implemented in `tasks.py`:

1. **add** - Creates tasks with optional `--priority`, `--tag` (repeatable), and `--due` flags
2. **list** - Lists tasks in id order, supports `--sort priority`, `--tag <tag>`, `--overdue`, `--today YYYY-MM-DD`
3. **done** - Marks task done by ID
4. **delete** - Removes task by ID
5. **priority** - Tasks show `(high)` or `(low)` suffix; medium has no suffix; `--sort priority` orders high→medium→low, ties by id
6. **tags** - Tasks show `#tag1 #tag2` suffix; `list --tag <tag>` filters
7. **due dates** - Tasks show `due:YYYY-MM-DD` suffix; `--overdue --today` filters open past-due tasks
8. **edit** - Replaces title via `--title NEW TITLE`
9. **search** - Case-insensitive title search
10. **export** - JSON array or CSV format output
11. **stats** - Shows open/done/total counts
12. **undo** - Restores previous state (survives between runs via history in tasks.json)

## Implementation Details

- Data stored in `tasks.json` (current working directory)
- Task IDs are integers starting at 1, never reused after deletion
- History for undo stored in tasks.json, persists between runs
- All errors print to stderr and exit 1
- Uses only Python 3 standard library

## Git Status

Initial commit exists. Code is ready for production use.
