# Does agent coordination add anything once a mature CI/CD pipeline exists? (experiment TRX-2)

**Status:** design frozen 2026-11-26 after the build and free checks, before any pilot run. Changes after the first measured run go
in the amendment log (section 10).

**Who built what:** an AI agent (Claude Code) designed and built this follow-up on top of [TRX](../2026-11-release-transition/)
(estate, simulator, oracle and scripts are reused) and will run, analyse and write it up. The owner asked for the experiment after
a critique of TRX (quoted in section 2) and asked for the next experiment to be run; publishing and merging wait for the owner.

## 1. Question

TRX found that independent agents shipped unsafe release transitions every time (0 of 25 safe, all with green CI), and that telling
them about the other change and asking for release constraints raised safe delivery to 80%. The critique: arm A had too little
engineering to stand for a mature enterprise pipeline, so TRX may only have measured the benefit of adding release engineering where
there was none, and some of arm B's gain may be deployment order and not safer code.

1. **With a mature pipeline in every arm, how safe is delivery, and what does it take to get there?** (first-time success, repair
   rounds, cost, time)
2. **Does agent awareness of concurrent changes add value on top of that pipeline?**
3. **Does an agent-written executable release plan add value on top of awareness?**
4. **Is any gain in the code, or in the deployment order?** (counterfactual: the same candidate released in the default order)

## 2. Why it is worth testing

The critique (a reviewer's, quoted by the owner): established practice already covers each TRX hazard (schema compatibility
checks, expand-and-contract migrations, idempotency and fault-injection testing, business-invariant tests, mixed-version testing,
deployment and rollback rehearsal); "TRX demonstrates the need for release engineering in an agentic SDLC. It does not demonstrate
the need for a new form of release engineering"; and "if mature conventional CI/CD performs just as well at a lower cost, publish
that". The plausible AI difference is scale and economics (many concurrent changes), which TRX did not test. This experiment tests the
narrower question the critique asks: does coordination add value beyond a mature pipeline, and at what cost?

## 3. What is being changed: the arms

Held constant: agent (Codex 0.157.0, hosted `gpt-5.6-luna`, medium effort, one turn per run, bubblewrap), estate, tickets, traffic,
fault schedule, oracle. **Every arm gets the same mature pipeline** after the two changes are merged:

1. unit tests (`mvn -o verify`) for each changed service;
2. a CI estate smoke on the all-new estate with generic checks;
3. a **mixed-version deployment rehearsal** of the arm's release order: rolling, one instance at a time, under test traffic, with a
   failed rollout and rollback injected once per changed service, checked by generic rules (statement consistency, duplicate
   postings, wrong decisions, ledger balance, rollback recoverable, dead letters, effects after a rule changed, deploy aborts).

A failed stage holds the release and goes back to **both** agents with the findings, for up to **two repair rounds**. A release that
is still held is not released (counts as not delivered).

| Arm | What the agents get beyond the ticket and `contracts/` |
| --- | --- |
| A | nothing: independent agents; the pipeline releases alphabetically, one instance at a time |
| B | the other ticket's title, a note that old and new versions run together and rollouts can fail, read-only `peers/` copies; no plan; the pipeline releases alphabetically |
| C | B plus an instruction to write `release/plan.json` (order, atomic switch, drain); the pipeline rehearses and executes the merged plan |

One variable per step: A to B adds awareness, B to C adds an executable plan.

## 4. The estate, scenarios, oracle and pipeline

As TRX (see its README): four small Java services, two instances each, delayed events, a failed rollout per scenario, an
independent oracle with scenario-specific invariants, six scenarios (S0 control, S1 event schema, S2 migration, S3 retries, S4
consent, S5 decision model). Reused unchanged: `estate/`, `sim/`, `refs/`, `build_estate.sh`.

**The pipeline is TRX's gate, run in every arm.** It uses generic rules (the simulator's `gate` mode), not the scenario-specific
oracle, but it shares the author, the simulator and the hazard vocabulary with the oracle. A free check (reference unsafe candidate
per scenario, no model): the pipeline held all five (S1, S2, S3, S4, S5) and admitted all five safe references plus the control. So it is
a best case for conventional controls on these hazards, not an average pipeline. Agent-written variants can still slip through: in TRX
the same rules admitted 3 of 25 candidates the oracle found unsafe, all on consent (S4).

Per trajectory the harness also records, for every candidate (held or not), the oracle's verdict if released as planned and if
released in the default order. That gives unnecessary blocking and the plan-versus-code split.

## 5. Measures

Read from files: oracle output (`release-*.json`), simulator timeline, merged diffs. Never agent summaries.

- **Primary: safe delivery** = released after the pipeline admits it (within two repair rounds), requirements work, zero oracle
  violations, rollback recovered. 0 or 1 per trajectory; a held release counts 0.
- **First-time success**: the pipeline admits the first candidate and the oracle finds it safe.
- **Repair rounds** (0 to 2), **cost per trajectory and per safe release** (tokens at list price: $0.20 input, $0.02 cached, $1.20
  output per million, repair runs included), **time** (seconds).
- **Unnecessary blocking**: rounds the pipeline held a candidate that the oracle would have judged safe and delivered.
- **Plan dependence** (arm C): final candidate safe as planned and unsafe in the default order.
- **Violations during the transition**: oracle violations on the released candidate, with the stage they occurred at.
- Reference column (not pooled): TRX's arm A with no pipeline: 0 of 25 safe, same estate and scenarios.

## 6. Hypotheses and analysis

Predictions in brackets, written before the pilot.

- **H1 (the pipeline carries most of the weight).** Arm A's safe delivery is far above TRX's 0% and below 100%. [about 70%; the pipeline
  holds almost every unsafe candidate, and the agents fix some of them from the findings but not all within two rounds.]
- **H2 (awareness helps efficiency, not final safety).** B has higher first-time success and fewer repair rounds than A, with final safe
  delivery within 10 points of A's. [first-time success A 15%, B 40%.]
- **H3 (the plan adds little on top of awareness).** C's final safe delivery is within 10 points of B's. [C may use fewer repairs
  but not reach higher final safety.]
- **H4 (cost).** Cost per safe release is lowest for B and highest for A. [Exploratory.]
- **H5 (blocking).** Unnecessary blocking is under 10% of candidates in every arm, and 0 on S0. [Exploratory.]
- **H6 (order).** Most of C's gain over B, if any, is plan dependence (unsafe in the default order). [Exploratory.]

Statistics as in TRX: score = mean over scenarios of each scenario's mean; one-sided permutation within scenario (100,000
shuffles, seed 1); bootstrap 95% intervals within scenario (10,000, seed 1); Holm within each hypothesis group. "Within 10 points"
hypotheses are judged on the 95% interval of the difference. Anything added after seeing data is labelled exploratory. If all arms reach
100%, that is a result: the differences are efficiency.

## 7. Size, cost and time

- Pilot: arm A only, 6 scenarios x 2 reps = 12 trajectories, about $0.5, 15 to 30 minutes.
- Main: 6 scenarios x 3 arms x 5 reps = 90 trajectories (pilot runs not reused), up to two repair rounds each. Estimate $4 to $10.
  **Ceiling $25.** Three trajectories in parallel, interleaved.
- **Pilot rule:** a scenario where arm A's first candidate is admitted and safe in every pilot run is kept but flagged "ceiling" (it
  cannot separate the arms); a scenario with login errors is rerun; if the pipeline holds the control (S0) falsely in the pilot, fix the
  pipeline before the main run and record it here.

## 8. Rounds (optional)

A pipeline that was not built around these hazards (variant hazards); concurrency at scale (20 agents, 12 services); a stronger model;
real services with latency.

## 9. Limits known in advance

- **The pipeline is built by me from the same rules and simulator as the oracle**, and held all five reference hazards; this is the
  best case for conventional controls. A real pipeline would catch some of these and miss others.
- Toy estate, one fault schedule, one model, five repetitions per cell; no statistics beyond intervals.
- TRX's arm A and this arm A differ in the pipeline, so the comparison with TRX is descriptive, not a controlled one.
- Scale and economics (many concurrent changes) are not tested.
- B bundles awareness of the peer ticket with a note about rollouts; I did not separate them.
- Login handling: the Codex login's refresh token rotates; a trajectory whose sessions hit a login error is not recorded.

## 10. Amendment log

| Date | Change | Why | Before or after a measured run |
| --- | --- | --- | --- |
| 2026-11-26 | First draft and build. | Owner's request after the TRX critique. | Before |
| 2026-11-26 | Pilot done (12 trajectories, arm A, $0.57): hazard scenarios safe 6 of 10 after up to two repair rounds (S1 2/2, S2 2/2, S4 1/2, S3 0/2, S5 0/2); the control admitted first time 2 of 2; none of the 10 hazard trajectories was safe at the first candidate, so no scenario is flagged ceiling; no login errors; no false holds. Pilot rule applied as written, design unchanged, main run launched (pilot not reused). | Pilot rule. | After the pilot, before the main run |
| 2026-11-26 | Main run done: 90 of 90 valid, $3.53, no login errors. Sign bug in printing lower-is-better differences fixed before reading results; legend relabelled. | Analysis hygiene. | After the main run |
