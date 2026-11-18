# Progress

## Session 1-3
- Implemented tasks.py with all commands (add, list, done, delete, edit, search, export, stats, undo)
- All feature flags included (priority, tags, due dates, sorting, filtering)
- F01 (add): PASSING - add creates tasks with auto-incrementing IDs
- F02 (list): PASSING - list prints tasks in id order, "No tasks" when empty
- F03 (done): PASSING - done marks task done, handles unknown ids

## Session 4
- F04 (delete): PASSING - delete removes task, preserves next_id, unknown id exits 1

## Session 5
- F05 (priority): PASSING - --priority high|medium|low works correctly
- Verified: add with priority shows suffixes (high)/(low), none for medium
- Verified: list --sort priority orders high, medium, low, ties by id
- Verified: invalid priority exits 1

## Session 6
- F06 (tags): PASSING - --tag repeatable, suffix '#work #home', list --tag work filters
- Verified: add with multiple --tag options appends tags in order
- Verified: list --tag work filters only matching tasks
- Verified: suffix order is priority then tags

## Session 7
- F07 (due dates): PASSING - --due YYYY-MM-DD, suffix 'due:YYYY-MM-DD' (after tags), invalid -> 'Invalid date: <v>', list --overdue --today DATE
- Verified: add with --due shows suffix after tags
- Verified: invalid date exits 1 with proper error message
- Verified: --overdue --today filters open tasks due before the given date
- Verified: suffix order is priority, then tags, then due

## Session 8
- F08 (edit): PASSING - edit ID --title NEW TITLE replaces title, prints 'Edited <id>'
- Verified: unknown id handling
- Verified: printed output correct

## Session 9
- F09 (search): PASSING - search TEXT does case-insensitive substring match on title, in id order
- Verified: search milk matches 'Buy Milk' and 'milkshake'
- Verified: no match prints 'No matches'

## Next: F10 (export)
