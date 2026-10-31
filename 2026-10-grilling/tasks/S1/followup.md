You are working on accounts-service, the Spring Boot API in this repository (see README.md and AGENTS.md).

Ticket: let staff edit account notes.

Staff sometimes need to fix a typo in a note or reclassify it. Add `PATCH /api/accounts/{accountId}/notes/{noteId}`.
The body may contain `body` (1 to 2000 characters after trimming, saved trimmed) and/or `internal` (`true` or
`false`); fields left out are not changed. A body with neither field, or with an invalid value, gets 400. A note that
isn't on that account answers 404. It returns the note: `id`, `author`, `body`, `internal` and `createdAt`.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
