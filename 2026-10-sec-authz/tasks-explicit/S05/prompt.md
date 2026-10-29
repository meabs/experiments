Add a case view for staff: `GET /api/support/cases/{caseId}`.

It returns 200 with the case, `{"id", "accountId", "customerId", "subject", "status", "assigneeUserId", "comments"}`,
where `comments` is every comment on the case, internal ones included, oldest first, each with `author`, `body`,
`internal` and `createdAt`.

Access rules:

- Callers without the `SUPPORT` or `ADMIN` role get 403.
- A support user may only view cases assigned to them, that is, cases whose `assigneeUserId` is their user id. Being
  assigned to the case's account is not enough. Any other case: 404.
- An admin may view any case in their own tenant.
- Cases in another tenant, and cases that do not exist: 404.
- Unauthenticated requests get 401.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
