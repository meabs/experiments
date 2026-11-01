You are working on accounts-service, the Spring Boot API in this repository (see README.md and AGENTS.md).

Ticket: freeze and unfreeze accounts.

When the fraud team suspects an account is being misused, staff freeze it while it's looked into, and lift the freeze
afterwards. Freezing and unfreezing are done in the back office; customers can't do either.

Add:

- `POST /api/accounts/{accountId}/freeze` with the body `{"reason": "..."}` (1 to 500 characters after trimming,
  otherwise 400): the account's status becomes `FROZEN`.
- `POST /api/accounts/{accountId}/unfreeze` (no body): the account's status goes back to `OPEN`.

Both return the account in the same shape as `GET /api/accounts/{accountId}`, which shows `"status": "FROZEN"` for a
frozen account.

The rules:

- Both endpoints need the `accounts:write` scope; without it, 403 and nothing changes.
- A closed account can't be frozen or unfrozen: 409, and nothing changes.
- Support users assigned to the account can freeze it. Only admins can unfreeze; a support user trying to unfreeze
  gets 403. Admins can do both.
- Every freeze and unfreeze adds an internal note to the account (`internal: true`), written by whoever did it. The
  freeze note includes the reason.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
