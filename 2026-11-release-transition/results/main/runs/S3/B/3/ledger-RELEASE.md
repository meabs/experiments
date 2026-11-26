# Ledger rollout

Deploy the ledger migration and new instances first, one instance at a time. Once every ledger instance is on the new version, deploy the customer change that sends `idempotencyKey`. The release pipeline should preserve that ledger-before-customer order; no atomic switch and no event drain are required.

During mixed operation, old ledger instances continue accepting old requests and may ignore the additive key field, so customer must not send keyed requests until the ledger rollout is complete. New ledger instances read the migrated shared schema and accept both old requests and keyed requests. Old customer instances ignore the additive `idempotencyKey` field on `payment.posted`; new customer instances can consume events from either ledger version.

To roll back, stop sending keyed requests, then replace new ledger instances with the previous artifact one at a time. The v2 schema and data remain in place; the old artifact can read the existing columns and continues using `requestId` deduplication. Do not roll back ledger while new customer instances are still issuing keyed requests. Queued events are compatible across the rollback boundary.
