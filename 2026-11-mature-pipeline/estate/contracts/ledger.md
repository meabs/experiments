# ledger (published contract)

Ops (all values are strings):
- `post {account, amount, requestId}` -> `{id, dup}`. `amount` is a decimal in major units ("12.50"). Posting the same `requestId` twice posts once (`dup=true`).
- `balance {account}` -> `{balance}` decimal in major units.
- `postings {account}` -> `{count, total}`.
- `health` -> `{status}`.

Events published:
- `payment.posted {account, amount, requestId}`; `amount` is a decimal string in major units. Consumed by `customer`.

Database: its own (table `postings`, schema migrations recorded in `schema_version`), shared by every instance and version.
