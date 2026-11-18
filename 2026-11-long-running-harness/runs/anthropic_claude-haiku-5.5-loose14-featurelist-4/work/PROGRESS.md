# PROGRESS

## Session 1
- Implemented F01 (`add TITLE` -> `Added <id>`) in tasks.py.
- Storage: tasks.json = {"next_id": int, "tasks": [{id,title,done}]}. Helpers load()/save()/fail() exist.
- Verified: two adds print Added 1 / Added 2 and tasks.json is written.

## Next
- F02 (list), then F03 onward in feature_list.json order.

## Session 2
- Implemented F02 (`list`: one line per task in id order, `No tasks` when empty) via task_line() helper.
- Verified manually; F02 marked passes=true.

## Next
- F03 (done), then F04 onward in feature_list.json order.

## Session 3
- Implemented F03 (`done ID`: marks done, prints `Done <id>`; unknown id -> `No such task: <id>` exit 1) via find_task()/parse_id() helpers.
- Verified manually; F03 marked passes=true.

## Next
- F04 (delete), then F05 onward in feature_list.json order.

## Session: F04 (delete)
- Implemented `delete ID` (prints `Deleted <id>`, unknown id -> `No such task`, ids never reused since next_id is persisted).
- Marked F04 passing in feature_list.json.
- Verified manually in a temp dir.
- Next: F05 (priority: --priority, suffix, --sort priority).

## Session: F05 (priority)
- Added parse_opts() helper for --option parsing; `add --priority high|medium|low` (default medium, stored per task), invalid -> `Invalid priority: <v>`.
- task_line() appends `(high)`/`(low)` suffix; medium shows none.
- `list --sort priority` orders high, medium, low, ties by id.
- Verified manually; F05 marked passes=true.
- Next: F06 (tags: repeatable --tag, `#a #b` suffix after priority, `list --tag X` filter).

## Session: F06 (tags)
- `add --tag X` repeatable (parse_opts gained a `repeatable` arg); stored as task["tags"].
- task_line() appends ` #tag` suffixes after priority; `list --tag X` filters (prints `No tasks` if none match).
- Verified manually; F06 marked passes=true.
- Next: F07 (due dates: --due, due:YYYY-MM-DD suffix, Invalid date, list --overdue --today).

## Session: F07 (due dates)
- Added `--due YYYY-MM-DD` on add (validated; `Invalid date: <v>` on error), stored as task["due"].
- task_line() appends ` due:YYYY-MM-DD` after tags.
- parse_opts gained `flags=` for boolean options; `list --overdue --today DATE` shows open tasks with due < DATE (--today defaults to real date).
- Verified manually; F07 marked passes=true.
- Next: F08 (edit --title).

## Session: F08 (edit)
- Added `cmd_edit`: `edit ID --title NEW TITLE` joins all args after `--title` into the title; prints `Edited <id>`; unknown id -> `No such task`.
- Verified manually (multi-word and quoted titles, unknown id, bad usage); F08 marked passes=true.
- Next: F09 (search TEXT, case-insensitive substring on title, `No matches`).

## Session: F09 (search)
- Added `cmd_search`: case-insensitive substring match on titles, id order, `No matches` when empty.
- Verified manually (MILK matches 'Buy Milk' and 'milkshake'; zzz -> No matches); F09 marked passes=true.
- Next: F10 (export --format json|csv).

## Session: F10 (export)
- Added `cmd_export`: `export --format json` (array of id/title/done/priority/tags/due, id order, due null when unset) and `export --format csv` (header, true/false, tags joined by `;`, empty due). Empty store JSON -> `[]`.
- Verified manually in a temp dir; F10 marked passes=true.
- Next: F11 (stats: open/done/total counts excluding deleted tasks).

## Session: F11 (stats)
- Added `cmd_stats`: prints `open: N`, `done: N`, `total: N` from current tasks (deleted tasks are gone).
- Verified manually; F11 marked passes=true.
- Next: F12 (undo via history snapshots stored in tasks.json).

## Session: F12 (undo)
- Added `record(data)` which pushes {next_id, tasks} snapshot into data["history"] before every successful add/done/delete/edit (called after validation, so failed commands aren't recorded).
- Added `cmd_undo`: pops the last snapshot, restores tasks and next_id, prints `Undone`; empty history -> `Nothing to undo` exit 1. History lives in tasks.json so it survives across runs.
- Verified manually (id reuse after undo of add, stepping through done/edit/delete, failed commands not recorded, cross-run). F12 marked passes=true.
- All features F01-F12 now pass. Next: nothing outstanding.
