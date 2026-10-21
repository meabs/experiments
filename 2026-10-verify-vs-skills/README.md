# Verification, skills or effort? (Codex)

Written 2026-10-21, before any task was built or any run made. Later changes go in the amendment log at the bottom.

## Why this follows skills-tasks

[2026-10-skills-tasks](../2026-10-skills-tasks/) found that Superpowers changed how Codex worked without making its changes more often correct:

- Superpowers ran the test suite in 28 of 32 runs, against 1 of 32 with no skills.
- It passed the same number of runs (24 of 32) at about three times the tokens.

Two leads came out of it ([REPORT.md](../2026-10-skills-tasks/REPORT.md)):

- **Unchecked success claims.** In 28 of 30 failed runs, the agent said its change worked.
- **Neighbour breaks.** On `HREVIEW`, 7 of 8 runs broke review creation while fixing review editing. They changed shared code and never checked its other use.

An external review also raised a clue about effort. `HREVIEW` passed both runs at high reasoning effort and failed all 8 at low effort. That suggests effort might matter more than skills.

This experiment asks which of three interventions buys the most correct changes per dollar:

- a short instruction to verify;
- a full skill pack;
- more reasoning effort.

## Question

On tasks where the obvious change compiles but is wrong at runtime, or breaks a neighbouring behaviour, which gives more verified-correct changes, and at what cost per correct change?

- a one-paragraph instruction to check the change against the running application, including the other uses of shared code it touches;
- the Superpowers skill pack;
- more reasoning effort (medium; first designed as high, see the amendment log).

## Agent and repository

- Codex `gpt-5.6-luna`, with the same clean home, isolation and rig version (AgentTrialRig `41da661`) as skills-tasks. Reasoning effort is **low** in arms A to C and **medium** in arm D (high until the amendment of 2026-10-21).
- shopizer at `6a4a0a6`, JDK 21, offline Maven. The verifier and isolation are reused from skills-tasks.

## Arms

| Arm | Name | Effort | What the agent gets | What it isolates |
| --- | --- | --- | --- | --- |
| A | `none` | low | The task prompt only | Baseline |
| B | `verify` | low | The task prompt, plus `AGENTS.md` holding the instruction below | Value of an explicit verification instruction |
| C | `superpowers` | low | The Superpowers pack, built exactly as in skills-tasks (same pinned commit, bootstrap through `AGENTS.md`) | What a full pack adds |
| D | `medium` | medium (was `high`; see amendment log) | The task prompt only | Value of more reasoning |

The instruction for arm B, fixed now and committed as `arms/verify/AGENTS.md`:

> Before you say you are done, check your change against the running application, not only by compiling it or by running the existing unit tests. Start the application, or write or run a test that starts it, and call the endpoints your change affects with the requests a client would send. Then find every other caller of any shared code you changed (services, mappers, populators, error handlers) and check that those callers still behave as they did before. In your final reply, say exactly what you ran and what you saw, and say plainly if you could not check something.

The rig cannot set a different effort per arm. So arm D runs as a second trial file (`trial-medium.toml`) with its own agent settings, otherwise identical. The two trial files are started together, so both cover the same hours.

Within each trial, the rig orders runs by repeat, then task, then arm, so arms A to C are interleaved within each task. The rig cannot randomise order.

## Tasks

The pool will have about 26 candidates of two kinds. Every task has a prompt written the way a user or support team would report it, an API-level hidden test, and a reference patch.

- **Neighbour-break tasks (*N*).** The natural fix changes code that another feature also uses, and the obvious version of that change breaks the other feature. Each has two kinds of hidden test:
  - target tests, which check the requested change;
  - `keeps…` tests, which check that the neighbouring feature still works.
- **Runtime-trap tasks (*R*).** The obvious change compiles and looks right but does nothing at runtime, or fails at runtime in a way that compiling and the existing suite do not show. `TAXRATE` from skills-tasks is the model. Some tasks may be reused from skills-tasks, with their tests unchanged.

How each task is checked (`scripts/validate.py`, results in `tasks/<ID>/validation.json`):

- At least one target test fails on the starting code, and every `keeps…` test passes on it, so the neighbouring feature works before the change.
- With the reference patch, every hidden test passes and so does the full existing suite.
- *N* tasks only, using a committed `naive.patch` that makes the obvious change:
  - at least one `keeps…` test fails with the naive patch;
  - the existing suite still passes with it, so the trap is real and the existing tests do not reveal it.

**Selection (fixed now).** Arms A and D each run every candidate twice in calibration, and those runs are discarded. Each candidate scores its calibration passes from A and D together (0 to 4). The 20 candidates with the lowest score are kept, with ties broken by the D score and then by task id.

Selecting on A and D favours those two arms slightly in the measured runs, through regression to the mean. That bias works against hypotheses H1 and H3 (B or C beating A), so those tests are conservative. It works in favour of D in comparisons with B and C, and the report will say so.

**Gate (fixed now).** The measured runs start only if at least 8 of the 20 kept tasks scored 0 or 1 of 2 for arm D in calibration. If they did not, the comparison with high effort would sit at the ceiling: I build more tasks, log the change here, and calibrate again.

## Size and cost

20 tasks × 4 arms × 3 runs = **240 runs**, plus about 104 calibration runs. Three runs per cell, not two, so that a difference within a task is not a single run.

From the measured costs in skills-tasks and skills-impact, a run costs about:

- $0.02 for A and B;
- $0.04 for C;
- $0.08 for D.

That comes to roughly $10 for the measured runs and $5 for calibration.

## Measures

**Primary:** verified pass. The build ran, every hidden test ran and passed, nothing was skipped, and no existing test failed. This uses the hardened `summarize.py`.

**Secondary:**

- **Cost per verified pass** (the decision measure): an arm's total list-price cost divided by its verified passes. Minutes and tokens per verified pass are reported too.
- **Neighbour breaks:** runs where any `keeps…` test fails. `summarize.py` now records the result of each hidden test.
- **False success claims:** failed runs whose end-of-run claim says the change works. Reported as a share of failed runs.
- **Process:**
  - Maven test runs;
  - whether the agent started the application or ran a test that boots it;
  - tests written;
  - test-file-first (`process.py` from skills-impact).

## Hypotheses and analysis (fixed now)

The unit of analysis is the task. For each task and arm, the result is passes out of 3. Comparisons use the per-task difference in passes between two arms.

| # | Hypothesis | Test |
| --- | --- | --- |
| H1 | `verify` raises the pass rate over `none` | One-sided exact sign-flip permutation test over tasks |
| H2 | `medium` (arm D) raises the pass rate over `none` | As H1 |
| H3 | `superpowers` raises the pass rate over `none` | As H1 |
| H4 | `verify` costs less per verified pass than `superpowers` | Per-task ratio of cost per pass, bootstrap over tasks; reported with its interval, not tested |
| H5 | `verify` has fewer neighbour breaks than `none` | One-sided sign-flip on the per-task difference in runs with a failing `keeps…` test (*N* tasks only) |

- H1 to H3 are Holm-adjusted together at α = 0.05. H5 is reported separately, unadjusted, and labelled secondary.
- Effects are the mean per-task difference in pass rate, with a bootstrap interval over tasks (10,000 resamples, seed 1).
- Also reported, two-sided and unadjusted, and labelled secondary: `verify` against `superpowers`, `verify` against `medium`, and `superpowers` against `medium`.
- Exploratory, and labelled as such:
  - results for *N* tasks and *R* tasks separately;
  - false-claim rates by arm;
  - whether arm B actually started the application.
- The analysis script, `scripts/analyse.py`, is written and committed before the measured runs.

## Known limits

- One repository, one agent and one model. Claude writes the tasks, hidden tests, reference and naive patches, and they are committed for review.
- Arm B's instruction mentions the kinds of shared code to check (mappers, services, error handlers). That is part of the intervention, not a leak: the instruction is the same for every task and says nothing about any one task.
- Arm D changes effort only, so its cost is not matched to the others. Cost per verified pass is how the arms are compared on cost.
- Arms B and C both add text through `AGENTS.md`, and arm C adds far more. They differ in length as well as in content.

## Amendment log

- 2026-10-21: design written at the user's request, following the skills-tasks report and its external review. Codex only.
- 2026-10-21 (before calibration), the candidate pool of 25:
  - **New tasks (8).**
    - Neighbour-break (*N*), each with a `naive.patch`:
      - `REVEDIT`: `HREVIEW` from skills-tasks, plus `keepsCreatingReviewsAndTheirRating`. Its naive patch is the actual diff of a failed skills-tasks run (`HREVIEW/none/1`), which broke review creation.
      - `PAGEVIS`: one handler serves the public and admin page lists.
      - `OPTORDER`: switching the option-value mapper from `sortOrder` to `order` breaks existing clients.
    - Runtime-trap (*R*):
      - `SUPERDEL`: the superadmin check compares groups with a string, and the obvious exception gives 500.
      - `CUSTLOGIN`: the admin password and email changes both break the login name. They were found as two bugs and merged, because they share a cause.
      - `CARTLAST`: reading an empty cart deletes it, and a null item set fails the totals.
      - `USERERR`: wrong statuses, including a lazy proxy that hides a missing user.
      - `BOXGET`: a box read by code loses its code, id and visibility, and its text comes back wrapped in CDATA.
    - All are real upstream defects found by probing the API. None is planted.
  - **Reused unchanged from skills-tasks (17).** `ADDR`, `AMBIG`, `AVAIL`, `CARTCALC`, `CATCOUNT`, `CATDUP`, `CONTENT`, `CUSTDUP`, `HCUST`, `MANCODE`, `MANINUSE`, `MANORDER`, `NOTFOUND`, `PAGE`, `REVIEW`, `TAXPAGE` and `TAXRATE`, all classed *R*. `HREVIEW` is replaced by `REVEDIT`. `CUSTPAGE` and `CUSTSEARCH` stay folded into `HCUST`.
  - **Prompts.** Some prompts name the neighbouring behaviour that must keep working (`PAGEVIS`, `OPTORDER`, `CARTLAST`, `BOXGET`, `USERERR`), as a ticket would. `REVEDIT` does not.
  - **Pool size.** About 26 candidates were planned and 25 were built.
  - **H4 calculation (before any run).** H4 is computed from each arm's *pooled* cost per verified pass, with tasks resampled for the interval. A per-task cost per pass is undefined whenever an arm passes no run of a task.
  - **Process measures added to `analyse.py` (exploratory).** "API-level test written": the diff adds a test that uses `TestRestTemplate`, `ServicesTestSupport` or `MockMvc`. "Started or called the app": a shell command runs `spring-boot:run` or `java -jar`, or calls localhost.

- 2026-10-21 (before calibration): full validation passed for all 25 candidates (`tasks/*/validation.json`). Two fixes came out of it. The hidden-test count in `verify.sh` and `validate.py` counted `@TestMethodOrder` as a test, and now matches `@Test` only. `SUPERDEL`'s test dropped `@DirtiesContext`, because restarting the Spring context broke an existing store-logo test.
- 2026-10-21 (after calibration of arm D at high effort, before any measured run): **arm D changed from high to medium reasoning effort**, at the user's request.
  - **Why.** High effort sat at the ceiling, and the gate would have failed. At the time of the decision, arm D at high effort had passed 28 of 29 calibration runs. Its only failure was `USERERR`, and it passed every task that arm A failed twice: `CARTLAST`, `REVEDIT` and `TAXRATE`. Arm A at low effort passed 36 of 50.
  - **Options considered.** Under the design, the alternative was to build harder tasks. Two rounds of calibration (skills-tasks and this one) showed that high effort solves nearly every task that can be verified here. Medium effort still tests whether more reasoning beats an instruction or a skill pack, and is less likely to sit at the ceiling.
  - **What changes.** Arm D runs at medium effort. It is renamed `medium` in the trial files (`trial-medium.toml`, `calibration-medium.toml`) and in `select_tasks.py` and `analyse.py`. H2 now reads "`medium` raises the pass rate over `none`".
  - **What stays the same.** The selection rule and the gate apply to arm D at medium effort, unchanged. Arm A's calibration at low effort is reused, as its settings have not changed.
  - **Where the record is.** The high-effort calibration is kept as a record in `results/calibration-high-effort.md`, and it is not part of the results.

- 2026-10-21 (after calibration, no measured run): **the gate did not pass.** Of the 20 tasks the rule kept, 7 scored 0 or 1 of 2 in arm D at medium effort; the gate needs 8 (`results/calibration.md`). Arm A at low effort passed 36 of 50 calibration runs, D at medium 39 of 50 and D at high 47 of 50 (`results/calibration-high-effort.md`). Two of the three neighbour-break tasks (`OPTORDER`, `PAGEVIS`) were passed by every calibration run in both arms and were not kept. Under the design, more tasks are built and calibrated before any measured run.
