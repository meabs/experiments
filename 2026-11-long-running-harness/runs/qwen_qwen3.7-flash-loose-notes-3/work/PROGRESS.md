# Progress

## Session 1
- Implemented tasks.py with all 12 features from SPEC.md:
  1. **add** - Creates tasks with optional --priority, --tag (repeatable), --due flags
  2. **list** - Lists tasks in id order, supports --sort priority, --tag filter, --overdue/--today
  3. **done** - Marks task done by id
  4. **delete** - Removes task by id
  5. **priority** - Tasks have high/medium/low priority; list --sort priority orders correctly
  6. **tags** - Repeatable --tag flag; list --tag filters by tag
  7. **due dates** - --due YYYY-MM-DD; list --overdue shows past-due open tasks
  8. **edit** - edit ID --title NEW TITLE replaces title
  9. **search** - Case-insensitive title search
  10. **export** - JSON and CSV export formats
  11. **stats** - Prints open/done/total counts
  12. **undo** - Reverts last mutating command (add/done/delete/edit), persists between runs via undo.json
- Data persisted in tasks.json, undo history in undo.json
- All imports are Python 3 standard library only
- Error handling: stderr messages with exit code 1 for all error cases
