I’ll trace the existing transactions endpoint and its tests, then add date-range parsing/validation while preserving ordering, access checks, and scope requirements. I’ll run the mandated offline Maven test suite afterward.

The endpoint currently delegates all transaction retrieval to one ordered repository method. I’m adding inclusive repository variants for lower-only, upper-only, and bounded ranges, with controller-level ISO date binding and explicit range validation; the existing no-filter method remains unchanged.

The offline test suite passes. The repository query methods use inclusive comparisons (`>=`, `<=`, `BETWEEN`) and retain the original `bookedOn DESC, id DESC` ordering; malformed date conversion and reversed ranges are mapped to the API’s 400 response.

Implemented date filtering for account transactions.

- Added optional inclusive `from`/`to` ISO date parameters.
- Added 400 handling for invalid dates and reversed ranges.
- Preserved ordering, response shape, access rules, and transaction scope requirements.
- Existing behavior remains unchanged when filters are omitted.

Verified with `mvn -o -q test`.