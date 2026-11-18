# Progress

## Session 1
- F01 (add): Already implemented and passing. Verified with tests.
- F02 (list): Implemented and verified with tests. Task list shows in id order, prints "No tasks" when empty. **PASSING**
- Next: F03 (done) - marks task done, prints 'Done <id>', unknown id errors out.

## Session 2
- F03 (done): Implemented and verified with tests. `done ID` marks task done and prints 'Done <id>'. Unknown id exits 1 with 'No such task: <id>'. **PASSING**
- Next: F04 (delete) - removes task, prints 'Deleted <id>', ids are never reused.

## Session 3
- F04 (delete): Implemented and verified with tests. `delete ID` removes the task and prints 'Deleted <id>'. Unknown id exits 1 with 'No such task: <id>'. Ids are never reused. **PASSING**
- Next: F05 (priority) - add with --priority high|medium|low, suffixes on task lines, list --sort priority, invalid priority error.
