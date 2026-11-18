# tasks.py specification

Build `tasks.py`, a command-line task manager. Python 3 standard library only.
Run as `python3 tasks.py <command> [args]`.

## General rules

- Data lives in `tasks.json` in the current working directory (create it on first write).
- Task ids are integers starting at 1. An id is never reused after a task is deleted.
- Success exits 0. Any error prints a message to stderr and exits 1.
- An unknown task id for `done`, `delete` or `edit` prints `No such task: <id>` to stderr.
- Task line format (used by `list` and `search`): `<id> [ ] <title>` for an open task and
  `<id> [x] <title>` for a done task. Suffixes are appended, in this order, each preceded by one space:
  priority (features 5), tags (feature 6), due date (feature 7). See each feature.

## Features

1. **add**: `add TITLE` creates an open task and prints `Added <id>`.
2. **list**: `list` prints one task line per task in id order. With no tasks it prints `No tasks`.
3. **done**: `done ID` marks the task done and prints `Done <id>`.
4. **delete**: `delete ID` removes the task and prints `Deleted <id>`.
5. **priority**: `add TITLE --priority high|medium|low` (default `medium`). A task line gets the
   suffix `(high)` or `(low)`; `medium` shows no suffix. `list --sort priority` orders high, medium,
   low, ties by id. Any other priority value is an error: `Invalid priority: <value>`.
6. **tags**: `add TITLE --tag work --tag home` (repeatable). A task line gets the suffix
   `#work #home` (tags in the order given, space separated). `list --tag work` shows only tasks
   with that tag.
7. **due dates**: `add TITLE --due YYYY-MM-DD`. A task line gets the suffix `due:YYYY-MM-DD`.
   An invalid date is an error: `Invalid date: <value>`. `list --overdue --today YYYY-MM-DD` shows
   only open tasks whose due date is before the given today (`--today` defaults to the real date).
8. **edit**: `edit ID --title NEW TITLE` replaces the title and prints `Edited <id>`.
9. **search**: `search TEXT` prints the task lines whose title contains TEXT (case-insensitive),
   in id order. With no matches it prints `No matches`.
10. **export**: `export --format json` prints a JSON array of objects with keys `id`, `title`,
    `done` (boolean), `priority`, `tags` (array) and `due` (string or null), in id order.
    `export --format csv` prints the header `id,title,done,priority,tags,due` then one row per task,
    `done` as `true`/`false`, tags joined with `;`, `due` empty when none. Titles never contain commas.
11. **stats**: `stats` prints three lines: `open: N`, `done: N`, `total: N`.
12. **undo**: `undo` reverts the most recent mutating command (`add`, `done`, `delete`, `edit`),
    restoring the previous state exactly, including the next id to be assigned. It can be repeated
    to step further back. It prints `Undone`. With nothing to undo it is an error: `Nothing to undo`.
    The history must survive between runs.
