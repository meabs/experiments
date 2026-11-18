# Progress

## Session 1
- **Completed F04 (delete)**: The delete command was already implemented in tasks.py. Verified all behavior:
  - `delete ID` removes the task and prints `Deleted <id>`
  - IDs are never reused after deletion (next_id continues incrementing)
  - Unknown ID prints `No such task: <id>` to stderr and exits 1
- Added test suite `tests/test_f04_delete.py` with 4 tests, all passing
- Marked F04 as passing in feature_list.json
- Created PROGRESS.md

## Session 2
- **Completed F05 (priority)**: Already implemented. Verified all behavior:
  - `add TITLE --priority high|medium|low` works (default medium)
  - Task line shows `(high)` or `(low)` suffix; no suffix for medium
  - `list --sort priority` orders high, medium, low, ties by id
  - Invalid priority value prints error to stderr and exits 1
- Added test suite `tests/test_f05_priority.py` with 6 tests, all passing
- Marked F05 as passing in feature_list.json

## Session 3
- **Completed F06 (tags)**: Already implemented. Verified all behavior:
  - `add TITLE --tag work --tag home` appends `#work #home` suffix
  - Tags shown in order given
  - `list --tag work` filters to only matching tasks
  - Suffix order: priority then tags
- Added test suite `tests/test_f06_tags.py` with 6 tests, all passing
- Marked F06 as passing in feature_list.json

## Session 4
- **Completed F07 (due dates)**: Already implemented. Verified all behavior:
  - `add TITLE --due YYYY-MM-DD` adds due date suffix `due:YYYY-MM-DD`
  - Invalid date prints error and exits 1
  - `list --overdue --today DATE` shows only open tasks due before today
- Added test suite `tests/test_f07_due.py` with 6 tests, all passing
- Marked F07 as passing in feature_list.json

## Session 5
- **Completed F08 (edit)**: Already implemented. Verified all behavior:
  - `edit ID --title NEW TITLE` replaces title and prints `Edited <id>`
  - Unknown ID prints `No such task: <id>` to stderr and exits 1
  - Preserves priority, tags, due date when editing
  - Multi-word titles supported
- Added test suite `tests/test_f08_edit.py` with 5 tests, all passing
- Marked F08 as passing in feature_list.json

## Session 6
- **Completed F09 (search)**: Already implemented. Verified all behavior:
  - `search TEXT` does case-insensitive substring match on titles
  - Results shown in id order with full task line format
  - Prints `No matches` when no results found
  - Works correctly with priority/tags/due suffixes
- Added test suite `tests/test_f09_search.py` with 5 tests, all passing
- Marked F09 as passing in feature_list.json

## Session 7
- **Completed F10 (export)**: Already implemented in tasks.py. Verified all behavior:
  - `export --format json` prints JSON array with id, title, done, priority, tags, due fields
  - `export --format csv` prints header row then data rows with done as true/false
  - Tags joined with `;` in CSV, due empty string when none
  - Empty store exports `[]` for JSON, header-only for CSV
  - Results sorted by id in both formats
- Added test suite `tests/test_f10_export.py` with 7 tests, all passing
- Marked F10 as passing in feature_list.json

## Session 8
- **Completed F11 (stats)**: Already implemented in tasks.py. Verified all behavior:
  - `stats` prints `open: N`, `done: N`, `total: N`
  - Fresh store prints zeros
  - Counts exclude deleted tasks
  - Mixed scenarios with open, done, and deleted tasks
- Added test suite `tests/test_f11_stats.py` with 5 tests, all passing
- Marked F11 as passing in feature_list.json

## Remaining Features
- F12: undo (revert last mutating command)
