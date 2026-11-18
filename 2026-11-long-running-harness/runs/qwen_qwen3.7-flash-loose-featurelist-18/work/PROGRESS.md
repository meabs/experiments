# Progress

## Session 1 - Fixed F07 (due dates and overdue filtering)
- Fixed broken `cmd_list` function: removed debug statements from list comprehension, properly initialize variables
- Implemented `--overdue` flag for `list` command to show only open tasks with due dates before today
- Implemented `--today DATE` option for custom today date (defaults to real date)
- Due date validation works correctly (`Invalid date: <value>` on error)
- Task line format correct: `<id> [ ] <title> (priority) #tags due:YYYY-MM-DD`
- Feature F07 marked as passing in feature_list.json
- Committed to git

## Remaining features (F08-F12):
- F08: edit command (partially exists but needs testing)
- F09: search command (exists but needs testing)
- F10: export command (exists but needs testing)
- F11: stats command (exists but needs testing)
- F12: undo command (exists but needs testing across runs)
