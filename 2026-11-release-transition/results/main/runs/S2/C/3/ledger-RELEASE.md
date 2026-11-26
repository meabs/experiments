# Ledger rollout

## Order

Deploy ledger instances one at a time in the pipeline's normal alphabetical order. No `deploy_after`, `atomic_with`, or queue drain constraint is needed. The first new instance runs the schema v2 migration at startup; subsequent instances see the recorded version.

## Mixed versions

Schema v2 adds `amount_cents` but retains legacy `amount`. New ledger instances write both columns and publish both `amount` and the additive `amountCents` event field. Old ledger instances ignore the new column and field and continue writing `amount`; new reads calculate from `amount_cents` and fall back to `amount * 100` for rows written by an old instance after migration. Old and new customer instances can consume either event shape because the existing `amount` field remains unchanged.

## Rollback

If the rollout fails, stop or roll back individual instances to the old ledger version. It can continue using the retained `amount` column and ignores `amount_cents`; postings created by the new version already contain the compatible legacy amount. Leave schema v2 in place—there is no destructive down-migration. Events already queued remain valid, and a later retry can resume the rollout.
