# Everything passed. Production failed. Can correct changes from separate agents break an estate in transit? (experiment TRX)

**Status:** design frozen 2026-11-26 after the build and free checks, before any pilot run. Changes after the first measured
run go in the amendment log (section 10). Codex access was tested first (hosted `gpt-5.6-luna` through `codex-bwrap.sh`,
`CODEX_PROFILE=hosted`; one real two-agent trajectory on the control scenario cost $0.015 and ran in 65 s).

**Who built what:** an AI agent (Claude) designed and built this experiment (estate, simulator, oracle, gate, scripts) and will
run it, analyse it and write it up. The owner proposed the idea and approved the design in outline, and asked the agent to
carry on through the pilot, the main run, the write-up and the merge without further sign-off.

## 1. Question

An agent's change can be correct as an artifact (it meets its ticket and its tests pass) and still be unsafe as a
*transition* (the live estate cannot move from the old state to the new one without breaking an obligation). Three questions:

1. **Does it happen?** When two agents each deliver a correct change to different services of a small brownfield estate,
   and the estate is deployed rolling, with one failed rollout that is rolled back, how often is a business invariant broken
   while every CI check is green?
2. **Does asking help?** If the agents are told about the other change and told to keep old and new versions compatible and to
   write release constraints (order, atomic switch, drain), does the transition become safe, or only the paperwork?
3. **Does a deterministic gate help, and what does it cost?** If an independent, non-AI rehearsal of the release on a staging
   copy admits or holds it (one repair round on a hold), does safe delivery rise without the gate simply blocking everything?

## 2. Why it is worth testing

- Parallel-agent research (Passes Alone, Fails Together, arXiv 2609.25396; NP-Bench, arXiv 2610.07261; CooperBench,
  2601.13295) asks whether patches **merge** and pass the same tests together. As far as I found (a quick search, abstracts
  and snippets only), none tests **live business correctness across a deployment**: mixed versions, persisted data, queued
  events, rollback. No novelty claim beyond "not found in this search".
- Earlier results here point the same way: agents' summaries and own tools mislead ([broken tools](../2026-11-broken-tools/),
  [complete gate](../2026-11-complete-gate/)); a rule match is not safe outcome ([GRD](../2026-11-guard-damage/)); a runnable
  gate beat a skill ([SEC-1](../2026-10-sec-authz/)); more orchestration did not help ([swarm tax](../2026-10-swarm-tax/),
  [split spec](../2026-10-split-spec/)).
- If B (told to coordinate) matches C (gate): coordination text is enough and the gate is overhead. If C wins and delivery holds:
  the check belongs outside the agents. If C wins only by holding releases: the gate is useless, and I say so.

## 3. What is being changed: the arms

Held constant: agent (Codex 0.157.0, `gpt-5.6-luna`, medium effort, one turn, bubblewrap, hosted), base estate, tickets,
traffic, fault schedule, oracle, and one repair round after a failed check.

| Arm | Each agent gets | Release |
| --- | --- | --- |
| **A** Independent | Its own service repository, its ticket, `contracts/` for all services. Nothing about the other change. | Default pipeline: unit tests, a CI smoke test of the all-new estate; changed services deploy alphabetically, one instance at a time. A failed CI check gets one repair round. |
| **B** Told to coordinate | A, plus: the title of the other team's ticket, read-only copies of the other services (`peers/`), a paragraph on rolling deployment, rollback and persisted state, and the instruction to keep versions compatible and to write `release/plan.json` (constraints: `deploy_after`, `atomic_with`, `drain_before`) and `release/RELEASE.md`. | As A, but the constraints from both teams are merged and executed (a cycle falls back to the default). |
| **C** Gate | B, plus a **transition gate** the pipeline runs on the merged candidate and plan. A hold (CI red or gate reject) gives each agent the report in **one** repair run; the gate runs again; a second reject means the release does not go out. | As B, only if admitted. |

B bundles awareness with the instruction (a real team gets both); C adds an independent check and its feedback loop on top
of B. A's and B's final candidates are also run through the gate afterwards, only for the record (its precision and
recall on agent-written changes); they do not act on the verdict.

## 4. The estate, scenarios, oracle and gate

**Estate** (`estate/`, plain Java 21, JUnit 5, H2, built offline with Maven, no frameworks): four services, `customer`
(profiles, consent, payments, a statement read model, credit applications, offers), `decision` (a score), `ledger`
(persistent postings, idempotent by `requestId`, schema migrations at start-up) and `notifier` (sends queued marketing
offers). Each is its own Maven project with its own tests. A simulator (`sim/`, never visible to the agents) runs the services
as two instances each, with a shared in-memory H2 database per service that survives every deployment, synchronous calls
between services, asynchronous events delivered three ticks later, and a virtual clock.

**Scenarios.** Five hazards plus a control. Each ticket pair (`scripts/tickets.py`) is legitimate, states the contract change
and says nothing about rollout; each change alone is correct; the original and the final estate are both correct.

| ID | Ticket 1 | Ticket 2 | Hazard in transit (default order is alphabetical) |
| --- | --- | --- | --- |
| S1 event schema | `ledger`: `payment.posted` carries `amountMinor` (integer), decimal `amount` retired | `customer`: statement read model uses `amountMinor` | A reader that knows only the new field meets old events (queued or from old instances): dead letters, statements diverge from the ledger. |
| S2 migration | `ledger`: integer `amount_cents` by start-up migration, `balanceCents` | `customer`: `availableCents` from `balanceCents` | A destructive migration cannot be rolled back after a failed rollout; mixed instances disagree on balances. |
| S3 retries | `ledger`: `idempotencyKey` | `customer`: retry on timeout, new `requestId` per attempt | New customer deployed before the new ledger: the retry is a different request to the old ledger, which posts twice. |
| S4 consent | `customer`: marketing needs explicit opt-in | `notifier`: daily send cap | Offers queued under the old rule are sent after the rule changed. |
| S5 decision model | `decision`: score 0 to 1000 | `customer`: thresholds 600 and 400 | During the window the wrong thresholds meet the wrong scale and decisions are wrong. |
| S0 control | `decision`: add `reason` | `customer`: pass `reason` on | None. The gate must admit it. |

**Release trajectory** = both agents work from the same base in separate repositories -> merged -> unit tests and a CI smoke
test of the all-new estate -> the plan is executed on the simulator: rolling deploy, an injected failed health check at
the scenario's fixed service (ledger for S1 to S3, notifier for S4, decision for S5 and S0) after its first instance is
upgraded, rollback, a recovery probe, then a retry -> traffic runs between every step.

**Oracle** (`sim/.../Run.java`, scenario traffic, reads the services' answers and the event log, never their health or the
CI): wrong or duplicated postings, statement against ledger, dead-lettered events, decisions against the reference policy,
offers sent after explicit consent became required (judged from the oracle's own seed data and the moment the last customer
instance switched), and whether the old version can serve the persisted data after rollback (writes and reads on every
instance). **Delivery:** the new requirements work on the final estate (acceptance probes per service and ticket).

**Gate** (`sim/.../Cli.java gate`, no model): a rehearsal of the same plan on a staging copy, once per changed service as
the failing one, with generic traffic (payments, applications, offers), lost ledger responses, and generic rules: P1 statements
equal the ledger, P2 no duplicate postings, P3 decisions equal the reference policy, P4 no effect after a rollout
contradicts the owner's current answer (consent), P5 rollback recovers, P6 ledger balances match intent, P7 no dead letters,
P8 no aborted deploy. **Overlap risk, stated plainly:** the gate and the oracle share an author, a simulator and a hazard
vocabulary. C therefore tests the value of a good gate plus its feedback loop on known hazard classes, not a gate's ability
to find an unknown one. Round 2 (section 8) would hold out hazards.

**Free checks (done before any model run, `scripts/selftest.py`, `results/selftest.json`):** for each scenario a
reference safe and a reference unsafe pair (`refs/`, generated by `scripts/refs.py`) passes every unit test and the CI smoke
test; the oracle calls the unsafe pairs unsafe (or the rollback failed) and the safe ones safe with the requirements
delivered; the gate rejects all five unsafe pairs and admits the five safe pairs and the control. S2's unsafe
migration really cannot be rolled back (the old version fails its health check against the migrated database). A gate that
holds everything would score zero delivery by construction.

**Pilot rule:** run arm A only, 5 scenarios x 3 repetitions (15 trajectories). A scenario in which A's released estate is
unsafe in under a third of the runs (nothing to prevent), or in which the agents fail their own ticket in more than a third
(a bad ticket), is retired or redesigned and marked `PILOT-ONLY`. Pilot trajectories of kept scenarios are not reused in the
main run.

## 5. Measures

Read from files, never from agent summaries: oracle output (`release.json`), the simulator's timeline, the merged diffs.

- **Primary: safe delivery** = released, the new requirements work in the final estate, zero oracle violations, rollback
  recovered. Per trajectory 0 or 1. A held or failed release counts 0.
- Secondary: **unsafe despite green CI** (released, CI green, violations or failed rollback); **delivered** (requirements work,
  regardless of violations); **violations** (count and kind); **recovered**; **held** (not released) and whether a hold
  was correct (reference verdict of the final candidate); **gate verdict on every arm's candidate** (precision and recall
  against the oracle); **false hold on S0**; process evidence counted from files (`plan.json` present, constraints used, diff
  size); cost per trajectory and per safe delivery.
- Cost from `turn.completed` tokens at list price ($0.20 input, $0.02 cached, $1.20 output per million), including repair
  runs; the simulator and gate cost nothing.

## 6. Hypotheses and analysis

Written before the pilot. Predictions in brackets.

- **H1 (the problem exists).** In arm A, at least half of the released-and-unsafe trajectories had a green CI. [about 90%:
  CI is green by construction unless an agent breaks its own ticket.]
- **H2 (instructions are not enough).** B's safe delivery is not above A's by a margin that survives correction. [B gains a
  little: plans get written and some hazards avoided (S3, S4), most (S1 tolerant reader, S2 migration, S5) not.]
- **H3 (the gate helps).** C's safe delivery exceeds B's and A's. [A about 25%, B about 40%, C about 70%.]
- **H4 (the gate is not a wall).** C's delivered rate on S0 is at least 4 of 5, and C's delivered rate overall is within 10
  points of B's. [C loses some deliveries to holds one repair round cannot fix.]
- **H5 (cost).** C costs more per trajectory than A but less per safe delivery. [Exploratory; costs are tiny.]

Test as in ELC/SDD/GRD: the score is the mean over scenarios of each scenario's mean; one-sided permutation within
scenario (100,000 shuffles, seed 1), bootstrap 95% intervals within scenario (10,000, seed 1), Holm correction within each
hypothesis group. H1 is a count with an interval. Anything added after seeing data is labelled exploratory.

## 7. Size, cost and time

- **Pilot:** 15 trajectories, arm A. About $0.30 (a trajectory is two agent runs, $0.015 on S0), 10 to 20 minutes.
- **Main:** 6 scenarios x 3 arms x 5 repetitions = 90 trajectories (if the pilot retires a scenario, it is dropped from the
  design for all arms), plus repair runs. Estimate $3 to $8. **Ceiling $25**; stop and report if reached. Three trajectories in
  parallel, interleaved by arm and scenario.
- Disk: per-run work folders are deleted after the result; patches, plans, logs and the simulator timeline are kept.
- **The replay viewer** ("the enterprise changing in real time"): generated from each trajectory's timeline into a
  self-contained HTML file in `diagrams/`; a reporting artifact, not a measure.

## 8. Rounds (optional)

Round 2: hazards the gate was not built around (a feature-flag removal, a cache-key change); a stronger model; agents allowed
to run the gate themselves while working; real HTTP services with latency instead of the in-process simulator; a bigger
estate.

## 9. Limits known in advance

- A toy estate (four services, hundreds of lines each), one deterministic fault schedule, one agent and model, five repetitions
  per cell. It shows whether the hazard and the gate's effect appear, not their rate in a real bank.
- Scenarios were chosen by me to contain a transition hazard; how often real changes contain one is not measured. The tickets
  state the contract change but not how to release it, which is the point and also a choice of mine.
- The default order is alphabetical, so arm A's outcomes depend partly on that convention; B and C can change it.
- The gate and oracle share an author, the simulator engine and the hazard vocabulary (see section 4). C's result is an upper
  bound on what such a gate does against unknown hazards.
- B bundles awareness with an instruction; agents cannot talk to each other during the run, so coordination is by documents.
- Simulated time and an in-process network miss real timing faults. Response loss and the failed rollout follow fixed schedules.
- Conclusions are about Luna at medium effort with Codex 0.157.0 only.

## 10. Amendment log

| Date | Change | Why | Before or after a measured run |
| --- | --- | --- | --- |
| 2026-11-26 | First draft. | Owner's idea; Codex access verified. | Before |
| 2026-11-26 | Design refined during the build: `events` service replaced by `notifier` (events are platform-level); release constraints in `release/plan.json` instead of a full plan; the gate became a rehearsal on a staging copy with generic rules; one repair round for every arm on a CI failure (C also on a gate reject); cost estimate cut from $10-18 to $3-8 after a real run cost $0.015; the 15-trajectory pilot is arm A only. | Found while building and testing the free checks. | Before (one smoke trajectory on S0, arm A, was run to test the pipeline and is not analysed) |
| 2026-11-26 | Pilot done (15 trajectories, arm A, $0.26): 15 of 15 released unsafe with CI green, 15 of 15 delivered their tickets; no scenario retired by the pilot rule. Design unchanged; main run launched (6 x 3 x 5 = 90, pilot runs not reused). | Pilot rule applied as written. | After the pilot, before the main run |
| 2026-11-26 | **First main run INVALID** (kept as `results/main-invalid-auth`, not analysed): 163 of 180 agent sessions died with `refresh_token_reused` (401). The shared login's refresh token was rotated by the per-run copies of the login and then lost when the per-run homes were deleted; the pilot and the first minutes of the main run worked on a still-valid access token. Fix: a refreshed per-run login is written back to the real one; a trajectory whose sessions hit a login error is not recorded, so a rerun redoes it. The numbers of that run (including the apparent "B and C no better than A") say nothing about the arms. | Mistake in my runner; found when cost per trajectory was a tenth of the pilot's and the control scenario did not deliver. | After the invalid main run; design unchanged |
| 2026-11-26 | Main run rerun after fresh login: 90 of 90 valid, $2.34. Replay viewer from section 7 dropped (not built). | Time; it is a reporting artifact, not a measure. | After the main run |
