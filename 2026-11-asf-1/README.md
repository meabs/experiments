# Does an open-source software factory beat a single coding agent? (experiment ASF-1)

**Status: pre-registered 2026-11-07, before any main run** (the user: "Push and do what yiu recommended"). The
smoke, the runner test and the arm A pilot are logged at the end. From here, the design changes only through an
amendment log that quotes the user.

## 1. Question

On hard feature tickets in a real Java codebase, does an existing open-source software factory, run as supplied,
produce more correct changes than one well-run coding agent? What does any gain cost?

The factory is **Machinist** (MIT, Go; github.com/owainlewis/machinist), run with its own prompts and its standard
pipeline. Fusion follows in ASF-2 (section 10).

## 2. Why it is worth testing

"Software factory" products promise that planning, hand-offs, independent review and repair loops make agents
deliver better software. Our own earlier results point the other way:
- SWT: one agent passed 57% of the hidden tests against a team's 26%.
- SPS: splitting the work did no better, at 2.3 times the cost.
- SWT and SPS: agent reviewers approved failing changes 24/24 and 14/15.

Those results came from setups we built ourselves. That leaves the obvious objection: "you built a straw-man
factory". This experiment tests someone else's factory, as published, so that objection does not apply.

## 3. The arms

**Same in every arm:**
- **Model:** `gpt-5.6-luna` at medium reasoning effort, in every role (triage, spec, build, review, repair).
  Any run in which any model other than Luna was called is excluded and reported (section 5).
- **Repository:** the same checkout: one commit, "shopizer", holding the tree of Shopizer `6a4a0a6` (tree
  `125f828`), with no upstream history. ELC's `setup.sh` makes this checkout for arm A. B and C get the same commit
  (`61a2a6f`) pushed as `main` of a fresh private repository per run. Every arm has the same pre-filled Maven cache.
- **Tickets:** the same ticket text, built by one function (`make_trial_a.ticket_text`): ELC's header line ("You are
  working in a checkout of shopizer…") and the ticket, which ends with its reply line.
- **Instruction files:** none added by us. No AGENTS.md and no skills.
- **Time limits (not equal, by design):** A has ELC's 3600 s per run. B and C keep Machinist's own stage limits as
  supplied: triage 30 min, spec 30 min, implement 120 min, review 45 min. Our runner cancels any B or C job still
  running after 3 hours, and the PR head at that point is graded.

| Setting | A: One agent | B: Machinist, single agent | C: Machinist, standard pipeline |
| --- | --- | --- | --- |
| What runs | `codex exec`, one turn, in our rig (bubblewrap, fresh home per run) | Machinist's **Single agent** mode: one Codex run does the task end to end inside Machinist | Machinist's **Standard pipeline**: Triage → Build → independent Review → up to 3 repair rounds on the same PR |
| Prompts | Ticket text only (no claim line) | Machinist's own, plus the ticket | Machinist's own, plus the ticket |
| Spec approval step | n/a | n/a | Stock: if triage asks for a spec, Machinist waits for approval before implement. Our runner approves at once, without reading or changing it, as a hands-off user would. Each approval is logged and counted |
| Delivered as | Diff of the working tree | Pull request in a private GitHub repository | Pull request in a private GitHub repository |
| What the comparison isolates | — | B vs A: does running inside the platform change anything? | C vs B: do the pipeline's stages add anything? C vs A: the headline |

**Run as supplied.** We do not tune Machinist's prompts, add our findings to it, or change its repair limit. We set
only the model, the pipeline mode and the access controls in section 6. If its documentation recommends a setting
for coding work, we use it and record it.

## 4. The tickets

We reuse ELC round 1's tickets (`../2026-11-evidence-led/tasks`). Their hidden tests have already been built,
validated and piloted, and they leave room to improve: ELC's vanilla arm, which matches arm A, passed 36% of the
hidden tests.

| Ticket | Kind | ELC vanilla, hidden tests passed (higher = easier) |
| --- | --- | --- |
| STOCK, PRODUCTDELETE, CUSTOMERCART, CATEGORYDELETE, SUPPORTORDERS, REVIEWS | Hard, cross-component bug reports | 22–56% per ticket |
| RETURNS, VISIBILITY | Easy (retired from ELC by its ceiling rule) | 17/17, 10/11 in the pilot |

- The **six hard tickets** carry the hypotheses.
- The **two easy tickets** answer a separate question: what does the factory cost on work one agent already gets
  right? They are reported on their own and are not in H1–H3.
- **Pilot rule** (amended before pre-registration, item 11 of the log): arm A gets one unscored run per ticket.
  The rule then uses that run together with ELC's five runs of the same setup (ELC vanilla), six runs in all. A
  hard ticket is dropped from H1–H3 only if most of those six runs are at the ceiling (100%) or at the floor (0,
  or the change doesn't compile). Result: no ticket is dropped, and all six hard tickets stay.
- None of ELC-H1's new tickets are used. They stay hidden from the user.

**Runs:** 8 tickets × 3 arms × 4 repeats = **96 runs**. Order is randomised within each repeat. Each run starts from
a clean copy of the base commit.

## 5. Measures

The primary measure is the first row. Higher or lower is better as stated.

| Measure | What it is | Better |
| --- | --- | --- |
| **Hidden tests passed** (primary) | Share of the ticket's hidden tests that pass on the delivered change. Each run is scored on its final state: the PR's head when the job ends in B and C, whatever Machinist's end state; the working-tree diff in A. A change that does not compile, or a run with no PR, scores 0. | Higher |
| Fully correct runs | Runs that pass every hidden test | Higher |
| Cost per run | All tokens from every Codex session in the run, from Codex's own session logs, at Luna's list price (input $0.20, cached input $0.02, output $1.20 per million tokens) | Lower |
| Tokens per run | Input, cached and output, by stage; shown in a token chart | Lower |
| Wall-clock time | From submit to delivered diff or PR | Lower |
| False green | Runs that report success, or whose reviewer approved, but fail hidden tests or the build | Lower |
| Human interventions | Approvals the run needed to finish (spec approvals in C). Each is logged and given at once, with no content added | Lower |
| Machinist end state (B, C) | complete, failed or blocked, and why. Reported separately from the score: a run is graded on its PR whatever its end state | — |
| Abandoned runs | Runs that stopped with no deliverable | Lower |
| Review effect (C only) | Hidden-test score before the first review vs after the last repair, scored on the PR's commits | Higher |

**Luna-only check.** Every Codex session log lists the model on each turn. A run counts only if every turn in every
session is `gpt-5.6-luna`. Any other model, or a call we cannot trace to a session log, excludes the run and is
reported.

## 6. Fairness and leak controls

- **The hidden tests stay out of the agent's reach.** Machinist itself runs on the host. It is not an agent, and
  its state is in `~/.machinist`. The only `codex` on its PATH is `scripts/codex-wrap.sh`, which runs each Codex
  session in its own bubblewrap sandbox, the same mechanism as arm A's rig (`local-setup/codex-bwrap.sh`):
  - `/home`, `/tmp` and `/run/user` are empty;
  - bound in: the job's workspace and the checkout's `.git`, Machinist's run folders, a Codex home holding a copy of
    the login and the pinned config (`model = "gpt-5.6-luna"`, `model_reasoning_effort = "medium"`), Codex and gh
    read-only, and the Maven cache as a throwaway overlay;
  - read-only roles (triage, review) get the workspace and `.git` read-only;
  - only GitHub and Machinist variables are passed in.

  Checked on 2026-11-07: the experiments folder, `~/.config`, Machinist's token and its database are invisible, and
  read-only roles cannot write.
- **Leak scan.** After each run, every session log is scanned for paths into the experiments folder, the hidden
  test names, and any `meabs/` repository other than run repositories. The experiments repository is public on
  GitHub. A hit voids the run.
- **No run sees another.** Each B and C run gets a fresh repository and checkout. Only the current run's repository
  is on the Machinist App installation. The token Machinist gives its agents reaches every repository on the
  installation, so detaching earlier runs closes that path.
- **Same Codex build in every arm:** 0.157.0 (the rig's `codex-pkg`, as in ELC), bound read-only into the sandbox.
- **Network and GitHub.** Every arm's sandbox shares the network, as in ELC. Only B and C have a GitHub token, scoped
  to the run's repository, because they deliver PRs. B vs A measures this together with the platform.
- **Grading** is the same for every arm. The deliverable is fetched as a diff, applied to a clean base, and graded
  with ELC's hidden-test runner. Grading happens on our side, never inside Machinist.

## 7. Hypotheses and analysis

The hypotheses use the six hard tickets. A run's score is its share of hidden tests passed. An arm's score is the
mean over tickets of that ticket's mean score.

| | Hypothesis | Test |
| --- | --- | --- |
| H1 (headline) | C scores higher than A | One-sided permutation test, labels shuffled within ticket, 100,000 shuffles, seed 1 |
| H2 | C scores higher than B: the pipeline adds something beyond the platform | Same |
| H3 | B differs from A: the platform alone changes something | Same, two-sided |

- **Correction:** Holm across H1–H3 at α = 0.05.
- **Effect sizes:** 95% bootstrap intervals, resampling runs within ticket, 10,000 resamples, seed 1.
- **Cost:** the cost ratios C/A and B/A, with bootstrap intervals. These are reported, not tested.
- **The easy tickets:** cost, time and pass rate per arm, described.
- **Scope of claims:** results apply to Machinist at the pinned commit, with Luna at medium effort, on these
  tickets. A difference that is not significant does not show the arms are equal.

## 8. Order of work

1. **Feasibility smoke, not scored.** One retired ELC ticket (LIMITS), run in B and C. Pass conditions:
   - every stage runs on Luna;
   - every token can be counted from the session logs;
   - a PR is opened and its diff applies and grades;
   - the leak scan finds nothing.

   Also record the timings and the cost, to set the time limit and confirm the budget. If Machinist cannot pin the
   model in every stage, the experiment stops there and we report that.
2. **Pin versions:** the Machinist commit, the Codex version and the Machinist configuration. Fill in the
   amendments, then ask before pushing the pre-registration.
3. **Pilot** arm A once per ticket (section 4).
4. **Main run:** 96 runs, one at a time. Running in parallel would let timings and rate limits interfere.
5. **Analysis and report.** The report covers impact, risks and configuration recommendations, with a token chart
   and real artefacts (a factory PR, review comments and repair rounds).
6. **Site PR**, then the Short with youtube.txt and its thumbnail.

## 9. Setup (approved by the user 2026-11-07: "Go and do it"; per-run repositories and gh: "Add rule and implement")

Pinned versions:

| Component | Version |
| --- | --- |
| Machinist | `4d7d776` (github.com/owainlewis/machinist), built with Go 1.26.6; config `~/.machinist/config.toml` sha256 `8920833bfe6d…` (stock) |
| Codex | 0.157.0 (`local-setup/codex-pkg`), in every arm |
| Model | `gpt-5.6-luna`, reasoning effort medium |
| GitHub CLI | 2.103.3 (Machinist and its agents; the system gh 2.46 is untouched) |
| Rig (arm A) | AgentTrialRig `e54514a` (0.7.0), `codex-bwrap.sh` sha256 `0daa3e0c3f8f…` |
| Grading | ELC `verify.sh` sha256 `ef2ab1768667…` and hidden tests as committed in `d902d92a` |
| Sandbox, JDK, Maven | bubblewrap 0.11.1, OpenJDK 21.0.12.1, Maven 3.9.12 |

Scripts:
- `scripts/make_trial_a.py` writes arm A's trial file;
- `scripts/run_bc.py` runs B and C (repository cycle, job, approval, cap, grading, evidence);
- `scripts/run-repo.sh` creates and detaches the per-run repositories;
- `scripts/grade.sh` and `scripts/evidence.py` do the grading and the Codex-log evidence.

## 10. Later

- **ASF-2: Fusion.** Same tickets and grading, with Fusion's built-in coding workflow (`builtin:coding`) and every
  lane (`planningModelId`, `executionModelId`, `validatorModelId`, `mergerModelId`, `titleSummarizerModelId`) set
  to Luna. To check first: whether Fusion accepts `gpt-5.6-luna`, and whether it can use our Codex login or needs an
  OpenAI API key.
- **ASF-1b: evolution.** Four changes in a row to the same application, each arm keeping its own previous work.
- **Evidence-bound arm.** Our playbook applied to whichever arm wins. This only runs after the stock comparison.

## 11. Cost and time estimate (from the smoke)

- Arm A: about $0.07 per run (ELC vanilla).
- Smoke on LIMITS: B $0.15 in 6 min; C $0.38 in 31 min (8 stages).
- The 96 runs come to roughly **$20** at list price.
- Wall-clock time is about 45 min per set of three arms, so the main run takes about **24 hours** run one at a time.

## Predictions (not findings)

- On the hard tickets, C will not beat A by much. Agent review has approved failing work before (SWT, SPS).
- C will cost clearly more.
- On the easy tickets, C will add cost and time with no gain in correctness.
- If the factory helps, it will most likely be through its repair rounds after review. The review-effect measure is
  there to show this.

## Smoke log and design changes (2026-11-07, before pre-registration)

1. **Sandbox moved to each Codex call.** Machinist runs triage and review with Codex's `--sandbox read-only`, which
   is itself bubblewrap. It cannot start inside another bubblewrap here, because Ubuntu's AppArmor rule blocks
   nested user namespaces. The first standard-pipeline smoke failed at triage with that error. Machinist now runs
   on the host. It is not an agent, and its state is in `~/.machinist`. The only `codex` on its PATH is
   `scripts/codex-wrap.sh`, which puts every Codex session in its own sandbox (as arm A's rig does), with the
   workspace and `.git` read-only for read-only roles. Checked: the experiments folder, `~/.config`, Machinist's
   token and database are invisible, and the read-only roles cannot write. Deviation: tool commands in read-only
   roles keep network access, which Codex's read-only mode blocks.
2. **Luna pin.** The wrapper adds `-c model="gpt-5.6-luna" -c model_reasoning_effort="medium"` to every call.
   Machinist's setup check (PING) uses Codex `app-server`, which chose `gpt-6-astra` even with the pin. That check
   is not a run, and it was run twice. Every job stage uses `codex exec`, which logged only Luna in the smoke.
3. **Contamination between runs. This is the main finding.** The standard pipeline's triage reported "existing
   partial work in commit 8749200". That commit was the single-agent smoke's solution, visible in Machinist's shared
   checkout. Machinist's triage prompt tells it to "find existing work before proposing a new change", so it will
   also look at earlier PRs, which GitHub never deletes. Change: **every run gets a fresh private repository**
   holding the base. After grading, the repository is removed from the App installation, so no later run can see
   it. It is deleted at the end.
4. **The review stage needs a newer GitHub CLI.** Machinist calls `gh api --slurp`, which gh 2.46 (Ubuntu's)
   lacks, so review failed. A current gh release goes on Machinist's PATH only.
5. **Dependabot** opened a PR on the new repository. It is disabled on every experiment repository.
6. Smoke results, not scored:
   - Single agent on LIMITS: 12/14 hidden tests, $0.147 (5.3M input tokens, 98% cached), about 6 minutes, Luna
     only, no leaks.
   - Standard pipeline: triage 100 s, implement 4 min (PR #3), then review failed (item 4). Its implement stage had
     the earlier solution in view (item 3).
7. **The user approved the per-run repositories and the gh download** ("Add rule and implement", 2026-11-07).
   - gh 2.103.3 (sha256 checked against the release checksums) is in `~/.local/gh-2.103.3`. It is first on
     Machinist's PATH and inside each agent sandbox, so Machinist and its agents use the same gh. The system gh is
     unchanged.
   - `scripts/run-repo.sh create|detach` does the per-run repository cycle.
   - GitHub accepts only a classic personal access token for adding a repository to, or removing one from, an App
     installation. The App's user token and gh's token both get 403.
   - The token Machinist gives its agents is the App user token. It reaches every repository on the installation,
     so only the current run's repository may be on it. `asf-shopizer`, which holds smoke PRs #2 and #3, comes off
     before any further run.
   - The experiments repository is public, and agents have network access. The leak scan also looks for
     `meabs/experiments` and `github.com/meabs`.
8. **Clean standard-pipeline smoke, on LIMITS in `meabs/asf-run-000` (job github_7c928e57). Not scored.**
   - Triage now reports "repository history contains no relevant in-progress change", so the fresh repository
     removes the contamination in item 3. The new gh fixed the review stage.
   - The job used all eight stages: triage, implement (PR #1), then three rounds of review and repair.
     - Every review asked for more changes.
     - The last implement stage pushed its fix commit (dd3168e). Its final JSON then put `pr_description` outside
       the `factory` object, so Machinist's strict parser rejected the reply ("json: unknown field
       pr_description") and the job ended `failed`. This is a model-output failure under stock Machinist, and it
       is kept as it is.
   - Hidden tests on the PR's final head: **11/14** (lower than the single agent's 12/14 in item 6, one run each).
     The failing tests are two checkout re-checks and `replacingAProductStoresItsNewLimits`.
   - Cost **$0.383**: 10.1M input tokens (94% cached) and 59.5k output tokens over 8 sessions. Every session was
     `gpt-5.6-luna@medium`, and the leak scan found nothing.
   - The leak scan now flags any `meabs/` repository except the run repositories, ignoring the API's `users/meabs/…`
     URLs.
   - **Proposed scoring rule (to be fixed in the pre-registration):** arms B and C are graded on the head of the
     run's PR when the job ends, whatever Machinist's final state is. That state (complete, failed or blocked) is
     reported as its own measure. A run with no PR scores 0.
9. **Arm A pilot**: one run per ticket, `results/pilot/A`, 2026-11-07. Hidden tests passed (higher is better):

   | Ticket | Arm A pilot (1 run) | ELC vanilla, same setup (5 runs) |
   | --- | --- | --- |
   | CATEGORYDELETE | 6/9 | 5/9 in all five |
   | CUSTOMERCART | **0/11, does not compile** (`maxCount` undefined in `OrderFacadeImpl`) | 2–3/11, all compile |
   | PRODUCTDELETE | **11/11** | 1/11 four times, 10/11 once |
   | REVIEWS | 1/10 | 1/10 four times, 7/10 once |
   | STOCK | 7/15 | 0, 0, 6, 8, 12 of 15 |
   | SUPPORTORDERS | 8/12 | 6–9/12 |
   | RETURNS (easy) | 14/17 | — |
   | VISIBILITY (easy) | 9/11 | — |

   - Cost: $0.02–0.09 per run. Every run ended `ok`.
   - The pilot rule in section 4, as drafted, drops CUSTOMERCART (floor) and PRODUCTDELETE (ceiling) on one run
     each. ELC's five runs of the same setup put both tickets well inside the range. Decided in item 11.
10. **B/C runner test** (`results/smoke2`): VISIBILITY in arm B, in `asf-run-001`.
    - The runner went through the whole cycle: create the repository, detach the previous one, submit the job, wait,
      grade, collect the evidence.
    - Result: 7/11 hidden tests, $0.18, 7 min, Luna only, no leaks.
    - Machinist's end state was `awaiting_merge`, which is how a single-agent job ends.
11. **Pilot rule amended after seeing the pilot, before pre-registration.** The user approved the recommendation
    ("Push and do what yiu recommended", 2026-11-07).
    - The rule now uses six runs per ticket: this pilot plus ELC vanilla's five. A ticket is dropped only if most of
      the six are at the ceiling or the floor.
    - Of the six hard tickets, CUSTOMERCART has 1 of 6 runs at the floor and PRODUCTDELETE 1 of 6 at the ceiling. No
      other run is at either. All six hard tickets stay.
    - Disclosed as a change made after seeing data. Under the old rule, H1–H3 would have used four tickets.
