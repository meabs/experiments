# Progress

## Session 1 - Implemented F01-F04 (Core CRUD)
- Implemented `tasks.py` with commands: add, list, done, delete
- Tests in tests/test_crud.py cover all 8 test cases
- All pass successfully

## Next
- F05: priority support (--priority high|medium|low)
- F06: tags support (--tag repeatable)
- F07: due dates support (--due YYYY-MM-DD)

## Session 2 - Implemented F05 (Priority support)
- Fixed `cmd_add` argument parsing to properly handle `--priority`, `--tag`, `--due` flags without consuming them as part of the title
- Priority suffixes work correctly: `(high)` for high, `(low)` for low, no suffix for medium
- `list --sort priority` orders by priority (high→medium→low), ties broken by id ascending
- Invalid priority values produce error message
- Updated test_sort_by_priority_ties_by_id assertion to match correct behavior
- All 15 tests pass

## Next
- F06: tags support (--tag repeatable)
- F07: due dates support (--due YYYY-MM-DD)

## Session 3 - Implemented F06 (Tags support)
- Fixed tag formatting: tags were joined without spaces between them
- Changed `" ".join(f"#{t}" for t in tags)` from `"".join` to `" ".join`
- Added tests/test_tags.py with 5 test cases covering single tag, multiple tags, tag filtering, priority+tag order, and no-tag case
- All 20 tests pass including the new F06 tests

## Session 4 - Implemented F08 (Edit command)
- Verified existing `cmd_edit` implementation works correctly
- Added tests/test_edit.py with 3 test cases: replace title, preserve other fields, unknown id error
- All 28 tests pass

## Next
- F09: search TEXT (case-insensitive substring on title)
- F10: export --format json|csv
- F11: stats command
- F12: undo command
