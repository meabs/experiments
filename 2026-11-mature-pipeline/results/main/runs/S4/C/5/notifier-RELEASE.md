# Notifier rollout

## Order

Notifier and customer must be switched atomically, all instances at once, with no traffic between the two versions. This prevents an old notifier from applying an offer after the new customer opt-in rule is active.

## Mixed versions

The new notifier creates the additive `offer_daily` table if needed and continues using the existing `sent` table. It counts sends already present in `sent`, including sends made by an old notifier instance, before applying the two-per-customer-per-platform-day limit. Before any send it calls the existing `customer.consent.check` operation, so queued offers from before the switch cannot bypass explicit opt-in. `sent` responses retain `count` and `ticks` and add `capped`.

## Rollback

If the rollout fails, switch both services back together before restoring traffic. Existing sends and queued events remain valid; the previous notifier ignores `offer_daily`, and the additive table is retained. A subsequent retry of the new version reuses that state. Because rollback restores the old customer rule at the same time, it does not leave a new customer policy paired with an old notifier.
