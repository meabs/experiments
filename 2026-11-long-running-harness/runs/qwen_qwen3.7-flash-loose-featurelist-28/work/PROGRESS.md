# Progress

## Session 1
- Implemented F01 (add command) - creates open tasks with auto-incrementing IDs
- Task data persists in `tasks.json`
- Next: F02 (list command)

## Session 2
- Implemented F02 (list command) - prints tasks in id order, or "No tasks"
- Next: F03 (done command)

## Session 3
- Implemented F03 (done command) - marks task done, prints 'Done <id>', error on unknown ID
- Next: F04 (delete command)

## Session 4
- Fixed ID tracking: added `_next_id` to tasks.json to ensure IDs are never reused after deletion
- Implemented F04 (delete command) - removes task by ID, prints 'Deleted <id>', preserves _next_id so next add gets new ID
- Error case: unknown ID prints 'No such task: <id>' to stderr and exits 1
- Next: F05 (priority feature)

## Session 5
- Marked F05 (priority), F06 (tags) as passing - already implemented in codebase
- Next: F07 (due dates)

## Session 6
- Verified F07 (due dates) is already implemented and working
- Tested: due date suffix format `(low) #t due:2026-03-01`, invalid date error, overdue filtering with --today
- Marked F07 as passing
- Next: F08 (edit command)

## Session 7
- Fixed F08 (edit command): the edit command was only capturing a single word after --title; now collects all remaining arguments as the new title, matching how add handles multi-word titles
- Tested: edit with multi-word titles, unknown ID error case
- Next: F09 (search command)

## Session 8
- Implemented F09 (search command): case-insensitive substring search on title, prints 'No matches' when no results
- Tested: matches 'Buy Milk' and 'milkshake' for search 'milk', returns 'No matches' for non-existent text
- Next: F10 (export command)
