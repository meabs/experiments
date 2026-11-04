Ticket: retry failed ledger postings automatically.

When the ledger doesn't answer, the payment is left at `POSTING_FAILED` and operations repost it by hand. That is slow
and error-prone.

Add a job, `LedgerRetryJob` in the `payment` package, with a public method `retryFailed()` that runs every 15 minutes
and retries the ledger posting of each `POSTING_FAILED` payment. A payment whose posting succeeds becomes `COMPLETED`.
Retry each payment at most 3 times; after that, leave it at `POSTING_FAILED` for operations.

Follow the existing conventions (README.md) and keep the existing behaviour and tests working.
