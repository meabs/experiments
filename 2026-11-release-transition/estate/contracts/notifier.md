# notifier (published contract)

Consumes `offer.queued {customerId, offerId}` (from `customer`) and sends the offer (a row in `sent`).
Ops: `sent {customerId}` -> `{count, ticks}` (ticks are the send times, comma separated). `health`.
