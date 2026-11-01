I’ll trace the existing transactions endpoint, its validation/error conventions, and tests, then implement date filtering with focused regression coverage and run the required offline Maven test suite.

The endpoint currently delegates visibility to `AccountService` and retrieves transactions through one ordered repository method. I’ll preserve that path and add bounded repository queries so filtering cannot alter access checks or ordering. Parsing will happen at the controller boundary, with invalid dates and reversed ranges mapped to the API’s existing 400 response.

The baseline suite and the previously excluded account API tests both pass with the implementation. I’m doing a final compatibility pass now, including preserving the original no-parameter service call path and checking the exact repository ordering/inclusivity behavior.

Implemented date filtering for account transactions.

- Added optional inclusive `from`/`to` date parameters.
- Invalid dates and reversed ranges return 400.
- Preserved ordering, visibility checks, scope requirements, response shape, and unfiltered behavior.
- Added repository queries for one-sided and bounded ranges.

Validation: `mvn -o -q test` passes.