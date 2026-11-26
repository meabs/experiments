# Customer release

## Rollout order

Deploy customer instances one at a time in the normal pipeline order. No
`deploy_after`, `atomic_with`, or queue drain constraint is required. Customer
does not need to wait for ledger to be fully deployed: its statement operation
accepts both the existing ledger response (`balance`, in major units) and the
CHG-102 response (`balanceCents`, in minor units).

## Mixed versions

The new customer version continues to return the existing `balance` and
`lines` fields and adds `availableCents`. It calls `ledger.balance` and prefers
`balanceCents`; while old ledger instances are serving traffic it converts the
legacy decimal `balance` response to an integer minor-unit string. Old customer
instances ignore the additive `availableCents` field and remain usable with
the ledger. Ledger should retain its legacy `balance` response during its
rollout so old and new customers can both call it.

## Rollback

If customer rollout fails, stop it and route traffic back to the old customer
instances. The shared statement data is unchanged by this release, and old
customer instances can continue serving it. If ledger is rolled back, retain
the legacy decimal response; the new customer version will use its fallback.
If customer is rolled back after ledger has deployed, the old customer version
continues to work because `availableCents` is additive and ledger retains
`balance`.
