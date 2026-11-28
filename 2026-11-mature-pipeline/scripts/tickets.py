"""Tickets for each scenario: one per service, as a team would receive them. They state the contract change and say
nothing about how to release it."""

T = {
 "S1": {
  "ledger": ("CHG-101: payment events carry minor units",
   "The platform's statement work needs money as integers. The `payment.posted` event must carry the amount as an integer number of "
   "minor units (pence) in a new field `amountMinor`, as a string, for example `1250` for 12.50. The decimal `amount` field is retired.\n\n"
   "Update the ledger service, its tests and `contracts/ledger.md`. The ops (`post`, `balance`, `postings`) keep working as they are."),
  "customer": ("CHG-101: statement read model uses minor units",
   "The ledger's `payment.posted` event now carries the amount as an integer number of minor units in `amountMinor` (a string such as `1250` "
   "for 12.50). The decimal `amount` field is retired. Change the statement read model to use `amountMinor`.\n\n"
   "Statement balances must stay correct. Update the customer service, its tests and `contracts/customer.md` if needed."),
 },
 "S2": {
  "ledger": ("CHG-102: store amounts as integers",
   "Postings must be stored as integers in minor units, in a new column `amount_cents BIGINT`, added by a schema migration that runs at "
   "service start-up (use the next `schema_version`). Existing postings must be migrated. `balance` must also return `balanceCents`, the "
   "balance as an integer in minor units (for example `725` for 7.25), alongside the existing `balance`.\n\n"
   "Update the ledger service, its tests and `contracts/ledger.md`. Existing ops keep working."),
  "customer": ("CHG-102: available balance for the mobile app",
   "`statement` must also return `availableCents`: the account's current ledger balance as an integer in minor units (a string such as `725` "
   "for 7.25), taken from the ledger's `balance` response field `balanceCents`.\n\n"
   "Update the customer service, its tests and `contracts/customer.md`."),
 },
 "S3": {
  "ledger": ("CHG-103: idempotency keys on payments",
   "`post` accepts an optional `idempotencyKey` (a string, stable for one payment). A second `post` with the same `idempotencyKey` returns the "
   "original posting with `dup=true` and posts nothing. `requestId` becomes a trace id for one call (a retry sends a new one) and is not the "
   "dedupe key when an `idempotencyKey` is given. Without a key, behaviour is unchanged.\n\n"
   "Update the ledger service, its tests and `contracts/ledger.md`. Schema changes go in a start-up migration (next `schema_version`)."),
  "customer": ("CHG-103: payments survive ledger timeouts",
   "`pay` must retry a timed-out `ledger.post`, up to 3 attempts in total, so that one lost response does not fail the payment, and one payment "
   "must still post exactly once. Send `idempotencyKey` = the payment's `ref` on every attempt and a fresh `requestId` for each attempt "
   "(`<ref>-<attempt>`, for tracing). After 3 timeouts return `status=FAILED`, `reason=timeout`.\n\n"
   "Update the customer service, its tests and `contracts/customer.md`."),
 },
 "S4": {
  "customer": ("CHG-104: marketing needs explicit opt-in",
   "Implied consent (legacy customers) no longer counts for marketing. `consent.check` returns `allowed=true` only when the customer's consent "
   "is `explicit`, and `offer` queues `offer.queued` only when allowed.\n\n"
   "Update the customer service, its tests and `contracts/customer.md`."),
  "notifier": ("CHG-104: daily cap on offers",
   "Send at most 2 offers per customer per day (day = platform tick / 100). Further offers that day are not sent; they are counted, and `sent` "
   "returns `capped`, the total number of offers dropped for that customer (as a string), in addition to `count` and `ticks`.\n\n"
   "Update the notifier service, its tests and `contracts/notifier.md`."),
 },
 "S5": {
  "decision": ("CHG-105: finer risk scores",
   "`score` now runs from 0 to 1000 instead of 0 to 100: `score = clamp(0, 1000, 1000 - amount*1000/income)` using integer arithmetic.\n\n"
   "Update the decision service, its tests and `contracts/decision.md`."),
  "customer": ("CHG-105: thresholds for the finer score scale",
   "The decision service's score is moving to a 0 to 1000 scale. `apply` must approve at a score of 600 or more, refer at 400 or more, "
   "otherwise decline, and return the score as given.\n\n"
   "Update the customer service, its tests and `contracts/customer.md`."),
 },
 "S0": {
  "decision": ("CHG-100: say why",
   "`score` also returns `reason`, a short string `ratio <n>%` where n = amount*100/income (integer arithmetic).\n\n"
   "Update the decision service, its tests and `contracts/decision.md`."),
  "customer": ("CHG-100: pass the reason on",
   "`apply` also returns `reason`, copied from the decision response when it has one (it is optional).\n\n"
   "Update the customer service, its tests and `contracts/customer.md`."),
 },
}

SERVICES = {s: sorted(T[s]) for s in T}

BASE_PROMPT = (
    "You own the `{svc}` service of a small banking estate (Java 21, Maven, JUnit 5, H2). This directory is your repository: `{svc}/` is "
    "your service and `contracts/` documents the published interface of every service. Your ticket is in TICKET.md. Implement it in `{svc}/`, "
    "update its tests, and make `mvn -o verify` (run inside `{svc}/`) pass. Change only `{svc}/`{extra_dirs}. "
    "When you have finished, reply with one short paragraph saying what you changed and what you checked."
)

COORD = (
    "\n\nCoordination. Another team is changing the `{other}` service at the same time, for the same release: \"{other_title}\". The services are "
    "deployed independently and rolled out one instance at a time, so old and new versions of both services run side by side; a rollout can "
    "fail part-way and be rolled back; and the databases and queued events keep their contents across deployments. Make your change safe to "
    "release together with theirs: keep old and new versions compatible with each other, prefer additive changes, and think about rollback.\n"
    "Read-only copies of the other services as they are today are in `peers/`.\n"
    "Write `release/plan.json` with your service's release constraints, as JSON with these optional keys: "
    "`deploy_after` (list of service names that must be fully deployed before yours), `atomic_with` (list of services that must be switched "
    "together, all instances at once, with no traffic in between), `drain_before` (true to wait until queued events are processed before "
    "yours is deployed), `notes` (free text). Constraints from both teams are combined and executed by the release pipeline; with none, "
    "services deploy alphabetically, one instance at a time. Also write `release/RELEASE.md`: rollout order, how it behaves while old and new "
    "versions run together, and how to roll back."
)

AWARE = (
    "\n\nAwareness. Another team is changing the `{other}` service at the same time, for the same release: \"{other_title}\". The services are "
    "deployed independently and rolled out one instance at a time, so old and new versions of both services run side by side; a rollout can "
    "fail part-way and be rolled back; and the databases and queued events keep their contents across deployments. Make your change safe to "
    "release together with theirs: keep old and new versions compatible with each other, prefer additive changes, and think about rollback.\n"
    "Read-only copies of the other services as they are today are in `peers/`. The release pipeline decides the rollout order."
)

GATE_REPORT = (
    "\n\nThe release pipeline held this release (its deployment rehearsal found problems). Report:\n{report}\n\nFix what is yours: change `{svc}/` (and `release/plan.json` if you "
    "were asked to keep one) so the release becomes safe, then make `mvn -o verify` pass. Reply with one short paragraph saying what you changed."
)
CI_REPORT = (
    "\n\nThe release pipeline's checks failed. Report:\n{report}\n\nFix what is yours in `{svc}/` and make `mvn -o verify` pass. "
    "Reply with one short paragraph saying what you changed."
)
