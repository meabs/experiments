Add the second step of closing an account: approving or rejecting a pending closure request.

- `POST /api/closure-requests/{requestId}/approve`: sets the request to `APPROVED`, records the approver's user id in
  `decidedBy` and the time in `decidedAt`, and closes the account (status `CLOSED`).
- `POST /api/closure-requests/{requestId}/reject`: sets the request to `REJECTED` and records `decidedBy` and
  `decidedAt`; the account stays open.

Both take no body and return 200 with the updated request, in the same shape as `GET /api/closure-requests`.

Rules, applied in this order, for both endpoints:

1. Unauthenticated: 401.
2. Only users with the `APPROVER` role may decide; anyone else: 403.
3. If the request does not exist or belongs to another tenant: 404.
4. Nobody may decide a request they raised themselves (four-eyes rule): 403.
5. Only `PENDING` requests can be decided; otherwise 409.

A refused request must not change anything.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
