# Progress Log

## Session 1 - Feature F01: add command
- Implemented `add` command that creates tasks with auto-incrementing IDs
- Tasks stored in `tasks.json` with JSON format
- History tracking for undo support built in from the start

## Session 2 - Feature F05: priority
- Added validation for priority values (high, medium, low) in `cmd_add`
- Invalid priority values now print "Invalid priority: <value>" to stderr and exit 1
- Priority suffixes already worked: "(high)" or "(low)" appended to task lines, medium has no suffix
- `list --sort priority` orders high, medium, low, ties by id
- Next: Implement F06 (tags)

## Session 3 - Feature F09: search
- Implemented `search TEXT` command with case-insensitive substring matching on title
- Prints task lines in id order for matches, or "No matches" if none found
- Next: Implement F10 (export json|csv)
