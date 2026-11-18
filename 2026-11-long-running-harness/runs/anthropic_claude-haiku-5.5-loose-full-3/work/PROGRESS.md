# Progress

- Implemented tasks.py per SPEC.md (stdlib only): add, list (--sort priority, --tag, --overdue/--today),
  done, delete, edit, search, export (json/csv), stats, undo.
- Undo history is stored in tasks.json under "undo" as snapshots (next_id + tasks), pushed only on
  successful mutations; persists across runs.
- Tests: tests/test_tasks.py covers F01-F12 plus failed-command-not-recorded. All pass; init.sh smoke ok.
- All features F01-F12 marked passing. Next: nothing outstanding.
