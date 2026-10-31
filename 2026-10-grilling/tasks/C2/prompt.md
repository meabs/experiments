You are working on accounts-service, the Spring Boot API in this repository (see README.md and AGENTS.md).

Ticket: filter the account list by status.

Add an optional `status` query parameter to `GET /api/accounts`: `OPEN` or `CLOSED`, exactly as written (upper
case). With it, the list keeps only the accounts with that status; without it, the endpoint behaves exactly as it does
now. Any other value gets 400. Who sees which accounts doesn't change.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
