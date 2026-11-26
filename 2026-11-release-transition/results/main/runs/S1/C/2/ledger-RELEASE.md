# Ledger release

## Rollout order

1. Fully deploy the customer CHG-101 version on all instances.
2. Deploy ledger one instance at a time.

There is no atomic switch and no queue drain requirement. The customer deployment must be complete before any ledger instance using this release is put into service.

## Mixed-version behaviour

The ledger `post`, `balance`, and `postings` operations retain their existing contracts and database representation. This release changes new `payment.posted` events to carry `amountMinor` as a decimal string containing integer pence; it does not emit the retired `amount` field.

The upgraded customer must consume both legacy events containing `amount` and new events containing `amountMinor`. Therefore events already queued by the old ledger remain processable while customer rolls out, and old ledger instances can continue publishing while ledger rolls out.

## Rollback

If this ledger release fails, stop routing traffic to the new instances and roll back to the previous ledger version. The upgraded customer must continue accepting legacy `amount` events, so rollback does not require an atomic customer rollback or database change. Events already emitted with `amountMinor` must also remain processable by the upgraded customer.
