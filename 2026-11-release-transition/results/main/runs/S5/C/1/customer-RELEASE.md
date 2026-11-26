# Customer release

## Rollout order

Roll out the new customer instances first, one at a time, until every customer
instance is new. Then roll out the new decision instances one at a time. This
is also the default alphabetical order (`customer` before `decision`); no
queue drain or atomic switch is required.

## Mixed-version behavior

The new customer understands both response formats from `decision.score`:

- scores above 100 use the new 0–1000 thresholds (approve at 600, refer at
  400);
- scores from the old 0–100 service use the legacy thresholds (approve at 60,
  refer at 40).

It returns the score unchanged. Therefore new customer instances can safely
call old decision instances while customer rollout is in progress, and can
continue doing so if decision is rolled back. Keeping customer rollout first
also prevents old customer instances from being exposed to the new score
scale.

## Rollback

If the customer release is rolled back, stop promoting new customer instances
and replace them with the previous version one at a time while the decision
service remains on its old version. If decision is rolled back after customer
has completed, leave the new customer version running: its legacy score path
is compatible with the old decision response. If customer must be rolled back
after decision has already been upgraded, roll decision back first, then roll
customer back one instance at a time.
