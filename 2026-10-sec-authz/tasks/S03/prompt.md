Ticket: approve or reject account closures.

Closure requests (`POST /api/accounts/{accountId}/closure-requests`) currently wait forever. Approvers need to be able
to decide them.

Add:

- `POST /api/closure-requests/{requestId}/approve`: the request becomes `APPROVED`, with the approver's user id in
  `decidedBy` and the time in `decidedAt`, and the account is closed (status `CLOSED`).
- `POST /api/closure-requests/{requestId}/reject`: the request becomes `REJECTED`, with `decidedBy` and `decidedAt`;
  the account stays open.

Both return the updated request in the same shape as `GET /api/closure-requests`. A request that has already been
decided cannot be decided again.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
