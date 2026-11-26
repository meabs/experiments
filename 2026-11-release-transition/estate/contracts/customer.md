# customer (published contract)

Ops (all values are strings):
- `create {customerId, consent}`; `consent` is `none`, `implied` (legacy customers) or `explicit`.
- `pay {customerId, account, amount, ref}` -> `{status}`: `OK`, or `FAILED` with `reason=timeout` when the ledger did not answer. Calls `ledger.post`.
- `statement {account}` -> `{balance, lines}`: read model built from `payment.posted` events.
- `apply {customerId, income, amount}` -> `{decision, score}`: calls `decision.score`; approve at a score of 60 or more, refer at 40 or more, otherwise decline.
- `offer {customerId, offerId}` -> `{queued}`: publishes `offer.queued {customerId, offerId}` when the customer's consent allows marketing.
- `consent.check {customerId, purpose}` -> `{allowed, basis}`.
- `health`.

Consumes: `payment.posted` (from `ledger`).
