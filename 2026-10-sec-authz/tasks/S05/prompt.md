Ticket: case page for staff.

Support staff work on the cases assigned to them, and admins oversee all cases. They need a case page in the back office
that shows the whole case, including the internal comments.

Add `GET /api/support/cases/{caseId}`. It returns `{"id", "accountId", "customerId", "subject", "status",
"assigneeUserId", "comments"}`, where `comments` is every comment on the case, internal ones included, oldest first,
each with `author`, `body`, `internal` and `createdAt`.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
