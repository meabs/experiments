# Progress

## Session 1 - F05 (Priority) Completed
- Fixed test_sort_by_priority assertion bug (was checking " b " in lines[1] but should check "[ ] a" since task "b" is high priority on line 0, task "a" is medium on line 1)
- All 34 tests pass
- Set F05 passes=true in feature_list.json

## Session 2 - F06 (Tags) Completed
- Verified all existing F06 tests pass (test_add_tags, test_filter_by_tag)
- Set F06 passes=true in feature_list.json

## Session 3 - F07 (Due Dates) Completed
- Verified all 5 F07 tests pass (test_add_due_date, test_invalid_date, test_overdue, test_overdue_excludes_done, test_suffix_order_priority_tags_due)
- The code already had full implementation for --due YYYY-MM-DD, invalid date validation, --overdue/--today filtering, and correct suffix ordering
- Set F07 passes=true in feature_list.json

## Next Feature to Work On
F08 (edit): `edit ID --title NEW TITLE` replaces title, prints 'Edited <id>'
