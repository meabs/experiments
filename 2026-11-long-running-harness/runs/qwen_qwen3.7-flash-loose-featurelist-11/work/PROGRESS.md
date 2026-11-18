# Progress

## Session 1
- Implemented `tasks.py` with all features (F01-F12) in one file
- F01 (add): **PASSING** - `add TITLE` creates tasks, prints "Added <id>"
- Committed initial implementation

### Next: F02 (list)

## Session 2
- Fixed CSV export syntax error (`\x27` escape sequences replaced with proper single quotes)
- Verified F02 (list): **PASSING** - empty list prints "No tasks", adds produce correct output
- Updated feature_list.json: F02 passes = true
- Committed fix

### Next: F03 (done)

## Session 3
- Verified F03 (done): **PASSING** - marks task done, prints Done <id>, handles unknown id with exit 1
- Updated feature_list.json: F03 passes = true
- Committed

### Next: F04 (delete)

## Session 4
- Verified F04 (delete): **PASSING** - removes task, prints 'Deleted <id>', ids never reused, unknown id exits 1
- Updated feature_list.json: F04 passes = true
- Committed

### Next: F05 (priority)

## Session 5
- Verified F05 (priority): **PASSING** - --priority high|medium|low, suffixes (high)/(low), list --sort priority, invalid priority error
- Updated feature_list.json: F05 passes = true
- Committed

### Next: F06 (tags)

## Session 6
- Verified F06 (tags): **PASSING** - `add TITLE --tag work --tag home`, suffix `#work #home`, `list --tag work` filters correctly
- Suffix order verified: priority then tags
- Updated feature_list.json: F06 passes = true
- Committed

### Next: F07 (due dates)

## Session 7
- Verified F07 (due dates): **PASSING** - `add TITLE --due YYYY-MM-DD`, suffix `due:YYYY-MM-DD` (after tags), invalid date error `Invalid date: <v>`, `list --overdue --today DATE` shows only open tasks due before today
- Updated feature_list.json: F07 passes = true
- Committed

### Next: F08 (edit)
