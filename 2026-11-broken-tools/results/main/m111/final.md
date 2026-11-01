I’ll inspect the transaction endpoint and existing validation/error conventions, then implement the date filters and run the offline Maven test suite.

The endpoint now accepts optional `LocalDate` bounds, validates the range before access/data lookup, and uses an ordered inclusive repository query with nullable bounds so unfiltered calls retain the same ordering and scope checks. I’m running the existing suite now.

The test command completed without errors. I also preserved the original no-filter service path and method overload, so callers without bounds use the exact existing repository query; filtered calls use the inclusive date predicates.

Implemented date-range filtering for account transactions.

- Added optional inclusive `from` and `to` ISO date parameters.
- Invalid dates and reversed ranges return 400.
- Preserved ordering, access controls, response fields, scope requirements, and unfiltered behavior.
- Verified with `mvn -o -q test` successfully.