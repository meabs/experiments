# Progress

## Session 1
- F07 (due dates) - PASSING. Verified all test steps:
  - `add TITLE --due YYYY-MM-DD` works correctly with suffix ordering
  - Invalid dates produce error message and exit code 1
  - `list --overdue --today DATE` shows only open tasks due before the given date
- Committed to git

## Next up
- F08 (edit): Edit task title, prints 'Edited <id>'
- F09 (search): Case-insensitive substring search on title
- F10 (export): JSON and CSV export formats
- F11 (stats): Open/done/total counts
- F12 (undo): Revert last mutating command across runs
