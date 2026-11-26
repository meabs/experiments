# Release plan

Deploy ledger first, one instance at a time, until every ledger instance is on the new version. Then deploy customer. No event drain or atomic switch is required.

During the ledger rollout, old customer instances continue sending the existing `requestId` field and both old and new ledger instances accept it with the existing behavior. The migration adds a nullable `idempotency_key` column and unique index; old ledger binaries continue to write rows because the new column is nullable. New customer instances must not be enabled until ledger is fully deployed, because old ledger binaries ignore the new key and cannot provide retry deduplication.

With ledger fully upgraded, old customer instances remain compatible because the key is optional. New customer instances can send a stable key with a fresh request trace id on retry; ledger returns the original posting and publishes only one event. The shared database and queued events survive deployment.

To roll back, stop the customer rollout first and return customer instances to the old version if any new customer instances are running. Then ledger may be rolled back one instance at a time; its additive schema remains compatible and old ledger instances ignore the nullable key column. If customer is rolled back after ledger, old customer remains compatible. Do not run new customer against an old ledger during rollback.
