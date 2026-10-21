# Engineering report: do popular agent skill packs improve code changes?

| | |
| --- | --- |
| Experiment | `2026-10-skills-impact` |
| Date run | 2026-10-21 (stage 1, 162 runs; no stage 2) |
| Design | [README.md](README.md), written and frozen before any measured run, with an amendment log |
| Harness | [AgentTrialRig](https://github.com/meabs/AgentTrialRig) 0.6.1 |
| Raw data | [results/](results/) |

## 1. Summary

We gave two cheap coding agents three real change tasks in a Java e-commerce codebase. Each agent ran with no skills, a placebo skill, or one of three widely promoted skill packs (Superpowers, Matt Pocock's skills, Cursor's pstack). A hidden test suite, run after each agent finished, decided whether the change was correct.

- **Correctness: no pack produced a measurable gain.** Superpowers passed 24/24 runs on the two hard tasks against 22/24 with no skills (p = 0.25). Pocock passed 19/24, and pstack 18/18 against an 18/18 control.
- **Process: the packs do what they say.** Superpowers made the agents write a test before the fix in 31 of 36 runs, against 0 of 36 with no skills, and every test it wrote failed on the buggy code before the fix.
- **Cost: the process costs 2 to 3 times the tokens.** The extra tokens go into tests and extra Maven runs. The production-code part of each change was the same size in every arm.
- **Failures came from understanding the domain, not from process.** All 11 failures were wrong models of the system: two bugs behind one symptom, and validation annotations that this codebase never runs. Writing tests first did not catch these when the tests encoded the same wrong model.

## 2. Question and approach

Skill packs are markdown instruction bundles that coding agents load on demand. The most visible ones promise better engineering discipline: test-driven development, systematic debugging, and "verify before you claim done". The question is whether they change outcomes that matter (correct changes, at what cost) on a real repository, not on a toy.

The approach is a controlled trial:

- Each condition (an "arm") changes only the skills installed in the repository.
- Each task has a reference solution and a hidden test written in advance.
- Pass or fail is decided by running the full Maven build with the hidden tests added, never by what the agent says.
- Hypotheses, decision rules and sample sizes were fixed in the design before any measured run.

## 3. Test setup

### 3.1 Agents

| Agent | CLI (as recorded by the rig) | Model | Settings |
| --- | --- | --- | --- |
| Codex | `codex-cli 0.157.0` | `gpt-5.6-luna` | Reasoning effort high, `danger-full-access` sandbox (the rig's own sandbox applies) |
| Cursor | `cursor-agent 2026.10.19-6bbf2c4` | `grok-4.7-low` | Default settings; the cheapest Grok model in Cursor |

The design listed Cursor CLI 2026.10.01. The CLI updated itself between design and run; every measured run used 2026.10.19, so no run is invalid under the "one version for the whole experiment" rule. Token totals are not compared between agents, because each CLI counts differently.

### 3.2 Repository

[shopizer](https://github.com/shopizer-ecommerce/shopizer) at commit `6a4a0a6`: a Spring Boot Maven multi-module platform (`sm-core-model`, `sm-core`, `sm-shop-model`, `sm-shop` and others) with about 1,200 Java files. It builds offline under JDK 21 against a pre-filled `~/.m2`. The REST layer has full-stack integration tests (`TestRestTemplate` against an H2 database), which the hidden tests reuse.

Three quirks of this codebase turned out to matter:

1. There is no bean-validation provider on the classpath, so `@Pattern`, `@Valid` and similar annotations compile but never run.
2. The manufacturer API's create and update methods catch every exception and return 503, so returning 400 needs an explicit check before that `try`.
3. Hibernate creates new columns itself (`hbm2ddl.auto=update`), so a new entity field needs no migration.

### 3.3 Arms

| Arm | Source (pinned) | Installed as | Visible to the model |
| --- | --- | --- | --- |
| `none` | - | nothing | built-ins only |
| `placebo` | written for this experiment | `.agents/skills/careful-engineering/SKILL.md`: 514 words of generic advice ("read before changing", "keep changes small"), with nothing on testing or verification | 1 skill |
| `superpowers` | `obra/superpowers` `b739a8a` | all 15 skills; the text its `sessionStart` hook injects is placed in `AGENTS.md` | 15, entry skill pre-loaded |
| `pocock` | `mattpocock/skills` `5beb35b` | the 27 skills in its plugin manifest | 11 (16 are `disable-model-invocation`) |
| `pstack` (Cursor only) | `cursor/plugins` `190d287`, pstack 0.15.29 | `.cursor/skills`, `.cursor/agents`, and a model rule setting every role to `inherit-parent`; each prompt is prefixed with `/poteto-mode` | `poteto-mode` pre-loaded; it reaches the other 55 skills by file path |

Notes on the treatments:

- **Superpowers' bootstrap.** Superpowers depends on a session hook. Plugin folders are blocked by isolation, so the hook's text was placed in `AGENTS.md`, which is how its Codex install guide wires it.
- **pstack's models.** pstack normally sends work to `grok-4.7-xhigh-fast` and `claude-opus-5-5-xhigh` subagents. Pinning every role to the parent model keeps the model under test fixed and the cost bounded; panel sizes are as shipped.
- **pstack's subagents.** pstack started subagents in only 10 tool calls: 9 on FEAT and 1 on CROSS.

`scripts/build_arms.sh` builds every arm from these commits and writes each arm's `SOURCE` file.

### 3.4 Isolation

A probe found that both CLIs load every skill in the user's home folder (`~/.agents`, `~/.claude`, `~/.cursor`, `~/.codex`), including installed copies of `tdd` and `using-superpowers`. Without isolation, the control arm would have carried the treatment. Isolation was set up as follows:

- **Codex** runs with a clean `HOME` and `CODEX_HOME` that hold only its login. This also hides the global `AGENTS.md` and Codex memories.
- **Cursor** cannot log in under a clean home. It runs with the real home, and the rig's `isolate` option (a macOS `sandbox-exec` profile) denies reads of the skill, plugin and agent folders.
- **Both** are denied this repository, which holds the hidden tests and reference patches.

A gate ([results/gate.md](results/gate.md)) asked each arm to list its skills before the measured runs. Its first run exposed a bug in the rig, described in section 7. The second run showed each arm seeing exactly the built-in skills plus its own pack.

## 4. Tasks

Each prompt describes a symptom or a requirement as a merchant would. It never mentions skills, tests or tools.

| ID | Kind | What the agent had to do | Hidden test |
| --- | --- | --- | --- |
| `BUG` | Bug fix | A merchant reports that specials with an end date never show on the storefront. Two independent slips were planted behind this one symptom: `PersistableProductAvailabilityMapper` stores the end date as the start date, and `ProductPriceUtils.finalPrice` checks the start date where it should check the end date. Both must be fixed. | 5 API tests: create a product through the admin API, read it back from the storefront API, and check `discounted` for each kind of date window |
| `FEAT` | Feature | A per-store cart line limit read from merchant configuration `CART_MAX_LINE_QUANTITY`, default 99. It applies on every storefront cart endpoint without a restart, returns 400, and leaves the cart unchanged; quantity 0 still removes the line. | 7 API tests: the default limit, limits above and below 99, every endpoint, and a live configuration change |
| `CROSS` | Multi-file | An optional manufacturer `website`: stored, settable through the private API on create and update, and returned in detail, list and product JSON. A value not starting with `http://` or `https://` gets 400 and is not stored. | 5 API tests against the JSON, including that a rejected update stores nothing |

Each hidden test fails on the starting code and passes with `tasks/<id>/reference.patch` applied. The full suite also passes with each reference applied. `scripts/setup.sh` replaces the clone's git history with a single commit, so the plant cannot be found with `git log` or `git diff`.

**Calibration** ([results/calibration.md](results/calibration.md)): a task was kept only if the control failed it at least once in three runs on one agent. BUG v1 (one slip) and BUG v2 (the other slip) were solved every time, so v3 combines them. FEAT stayed at the ceiling after one round of making it harder. It was kept for its cost and process measures, and excluded from the pass-rate tests before the run. CROSS was kept as first written.

## 5. Grading pipeline

Each run went through the same steps:

1. The rig clones the repository, applies the arm's overlay, runs `setup.sh` (plant and history reset), then runs the agent with a 20-minute limit.
2. `verify.sh` saves the agent's diff, copies in the hidden tests and runs `mvn -o clean test` across the whole reactor with `-Dmaven.test.failure.ignore=true`, so a failing module cannot hide later ones.
3. `summarize.py` reads the surefire XML. **Pass** means Maven ran, every hidden test passed, and no other test failed, including tests the agent added. A change that leaves the build red would not merge, so it does not pass.
4. With `claim = true`, the agent ends with a structured line saying what it ran and whether it passed. An **overclaim** is a run that says `passed` but fails grading.

Two later checks are measured from the saved diffs:

- **Tests that bite** (`bite.sh`): the run's own test changes are applied to the planted, unfixed code and run. A failure means the test detects the bug.
- **Test-first**: from the order of the run's edits, whether the first edit under `src/test` came before the first under `src/main`. Codex edits are read from `file_change` events and Cursor's from `edit` tool calls.

`reverify.sh` regrades any run from its saved diff on a fresh clone. It was used during calibration and is how anyone can check a grade.

## 6. Results

### 6.1 Execution

| | Codex | Cursor |
| --- | --- | --- |
| Runs | 72 (3 tasks × 4 arms × 6) | 90 (3 tasks × 5 arms × 6) |
| Wall time | 1 h 35 min | 1 h 40 min |
| Crashes, timeouts, infrastructure reruns | 0 | 0 |

Repetitions were interleaved, so no arm ran as a block, with 3 runs in parallel. The whole stage took about 3.5 hours, against an estimated 7.

### 6.2 Pass rate

| Task | Agent | `none` | `placebo` | `superpowers` | `pocock` | `pstack` |
| --- | --- | --- | --- | --- | --- | --- |
| BUG | Codex | 6/6 | 4/6 | 6/6 | 5/6 | - |
| BUG | Cursor | 6/6 | 6/6 | 6/6 | 5/6 | 6/6 |
| CROSS | Codex | 4/6 | 4/6 | **6/6** | 4/6 | - |
| CROSS | Cursor | 6/6 | 6/6 | 6/6 | 5/6 | 6/6 |
| FEAT | Codex | 6/6 | 6/6 | 6/6 | 6/6 | - |
| FEAT | Cursor | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |

Cursor with `grok-4.7-low` solved every task in every control run, so only Codex left room for a pack to help. That gives 12 Codex runs per arm on the tasks that discriminate.

### 6.3 Pre-registered hypotheses

All tests are one-sided Fisher exact tests against `none`, at α = 0.05, as fixed in the design.

| # | Claim | Treatment | `none` | p | Verdict |
| --- | --- | --- | --- | --- | --- |
| H1 | Superpowers raises the pass rate (BUG + CROSS) | 24/24 | 22/24 | 0.245 | not supported |
| H2 | Pocock raises the pass rate (BUG + CROSS) | 19/24 | 22/24 | 0.951 | not supported |
| H7 | pstack raises the pass rate (Cursor, 3 tasks) | 18/18 | 18/18 | 1.000 | not testable (ceiling) |
| H4 | Superpowers' BUG runs write a test that bites | 12/12 | 8/12 | 0.047 | supported, narrowly |
| H4 | Pocock's BUG runs write a test that bites | 12/12 | 8/12 | 0.047 | supported, narrowly |
| H4 | pstack's BUG runs write a test that bites | 5/6 | 8/12 | 0.439 | not supported |
| H5 | Superpowers works test-first | 31/36 | 0/36 | < 0.001 | supported |
| H5 | Pocock works test-first | 10/36 | 0/36 | < 0.001 | supported |
| H5 | pstack works test-first | 6/18 | 0/18 | 0.010 | supported |
| H6 | Fewer overclaims (descriptive only) | Superpowers 0, pstack 0, Pocock 4 | 2 | - | see 6.6 |

Points that affect how these read:

- **The placebo control.** The placebo passed 20/24 and was never test-first (0/36), so the process effects come from what the packs say, not from adding skill text.
- **H4 is weaker than its p-value suggests.** All 44 runs that wrote a test produced one that failed on the unfixed code. The difference between arms is therefore only whether a test was written at all. Three H4 comparisons were made, and p = 0.047 would not survive a correction for that.
- **H5 does not depend on how test-first is counted.** It holds whether the share is taken over all runs (above) or only over runs that edited both test and production code (Superpowers 31/35 against 0/10).

### 6.4 Cost and effort

Medians per run, with tokens relative to `none` for the same agent and task:

| Agent | Arm | Tokens vs `none` | Turns | Maven runs | Production lines changed | Test lines changed | Seconds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Codex | none | 1.00x | 24 | 3 | 50 | 0 | 134 |
| | placebo | 1.25x | 30 | 4 | 46 | 25 | 161 |
| | pocock | 1.74x | 27 | 5 | 43 | 74 | 192 |
| | superpowers | 2.77x | 34 | 8 | 44 | 129 | 307 |
| Cursor | none | 1.00x | 44 | 1 | 51 | 0 | 118 |
| | placebo | 1.05x | 48 | 1 | 41 | 0 | 116 |
| | pocock | 1.49x | 47 | 1 | 38 | 21 | 149 |
| | pstack | 2.75x | 67 | 2 | 44 | 38 | 206 |
| | superpowers | 2.33x | 64 | 3 | 51 | 74 | 170 |

The packs leave the production change the same size, about 40 to 50 lines in every arm. All of the extra diff is tests, and most of the extra tokens go into writing them and into extra build-and-test cycles. The rig's bootstrap intervals for relative cost exclude 1.00 for Superpowers, pstack and Pocock on both agents ([results/report.md](results/report.md)).

**Spend:**

| Agent | Tokens | Price | Cost |
| --- | --- | --- | --- |
| Codex | 72 runs | $0.20 fresh input, $0.02 cached input, $1.20 output, per million | **$7.85** |
| Cursor | 7.7M fresh input, 60.4M cache reads, 0.9M output | full $2 per million on cache reads (the design's rule) | $141 (upper bound) |
| Cursor | same | $0.20 to $0.50 per million on cache reads | $33 to $51 |

The design's estimate of $10 to $50 assumed 30k to 80k tokens per Cursor run, taken from an earlier experiment's question-answering runs. Change runs used 0.4M to 1.2M tokens. The actual Cursor charge is on Cursor's usage dashboard.

### 6.5 Skill uptake

Uptake is the share of runs that read a `SKILL.md`; a pack that is never read cannot help.

| | `placebo` | `superpowers` | `pocock` | `pstack` |
| --- | --- | --- | --- | --- |
| BUG | 12/12 | 12/12 | 12/12 | 6/6 |
| CROSS | 12/12 | 12/12 | **1/12** | 6/6 |
| FEAT | 12/12 | 12/12 | **5/12** | 6/6 |

Pocock's skills are triggered by matching their descriptions. A bug report matched `diagnosing-bugs`, but feature and multi-file requests rarely matched anything. Under the design's rule (uptake under 50%), Pocock's null result on CROSS and FEAT means the skills were rarely used, not that they do not work when used. Superpowers' always-loaded bootstrap is why it was read in every run.

### 6.6 Overclaims and self-reports

| Agent | Arm | Said `passed` | Overclaims |
| --- | --- | --- | --- |
| Codex | every arm | 70 of 72 runs | 2 none, 3 placebo, 3 pocock, 0 superpowers |
| Cursor | none | 5/18 (13 said `not-run`) | 0 |
| Cursor | placebo | 2/18 | 0 |
| Cursor | pocock | 10/18 | 1 |
| Cursor | pstack | 11/18 | 0 |
| Cursor | superpowers | 18/18 | 0 |

Codex said `passed` in 70 of 72 runs whatever happened, so on Codex the overclaim count is just the failure count. Superpowers' zero overclaims there reflects its zero failures, not more honest reporting. On Cursor the packs had a clear effect on behaviour. With no skills, Cursor usually compiled and stopped, and said so (`not-run`). With Superpowers it ran the tests and reported `passed` in every run, as `verification-before-completion` instructs.

### 6.7 Failure analysis

Each of the 11 failures was read in its diff and Maven log. None was an infrastructure fault.

| Failure | Runs | What happened |
| --- | --- | --- |
| Half a fix | 4 BUG runs: Codex placebo ×2, Codex pocock, Cursor pocock | The agent found one of the two slips, fixed it, and wrote a unit test of that unit, which passed. The merchant's symptom remained, because the other slip still broke the API path. All 4 claimed `passed`. |
| Validation that never runs | 5 CROSS runs: Codex none ×2, Codex placebo, Codex pocock, Cursor pocock | The website was "validated" with `@Pattern` or a similar annotation, or the check sat inside the `try` that converts every exception to 503. An invalid website was stored. Nobody posted an invalid value to the running API. |
| Validation that broke the API | 2 CROSS runs: Codex placebo, Codex pocock | To make `@Pattern` run, the agent added `spring-boot-starter-validation`. That switched on validation for every endpoint, and existing category and product creation tests failed with 400. |

These failures share a pattern. Each run wrote tests that matched its own model of the system, and the model was wrong. A unit test of `ProductPriceUtils` cannot reveal that the mapper stores the wrong date, and a test that inspects the annotation cannot reveal that nothing evaluates it. Superpowers avoided all of these on Codex (12/12 on BUG and CROSS). API-level testing does not fully explain this. On those two tasks, Codex wrote a test through the REST API (`TestRestTemplate`) in 5 of 12 Superpowers runs, 4 of 12 Pocock runs (which still failed 3 times), and 1 of 12 `none` runs. Cursor never did. At this sample size, Superpowers' clean record may be chance (H1, p = 0.25).

## 7. Engineering issues found along the way

These came up while building and checking the setup, before any measured run. All are fixed, and each is recorded in the amendment log or the calibration notes.

| Issue | Effect if missed | Fix |
| --- | --- | --- |
| Home-folder skills are visible to every arm | The control carries the treatment | Clean `HOME` for Codex; `isolate` for Cursor; a gate run before measuring |
| The rig's `isolate` denied the ancestors of the work folder, and both CLIs silently skip project skills when they cannot read ancestor metadata | Every treatment arm silently becomes `none` | Rig change: allow `file-read-metadata` on each ancestor (not its contents), with a test |
| The first sandbox profile was malformed (zsh did not split the folder list), so it blocked nothing | Isolation silently off | Pass the folders as an array; probe again |
| A stale compiled hidden test in `target/` | False failures | The verifier always runs `clean` |
| The hidden test copied into the wrong module (`sm-core` instead of `sm-shop`) | All of BUG v2 calibration graded as failed | Path fixed; the 6 runs regraded with `reverify.sh`: 6/6 |
| Maven stopped at the first failing module | A red `sm-core` hid the hidden test in `sm-shop` | `-Dmaven.test.failure.ignore=true` plus a surefire XML parser; an early inline parser gave a false pass and was replaced |
| The plant patch captured a binary `.dat` file that the tests modify | Patch conflicts | Patches restricted to Java files |
| `--retry-failed` reruns timeouts | Timeouts, which the design counts as failures, would be quietly retried | Not used |

Two rig features were added for this experiment: an arm-level `prompt_prefix` (for `/poteto-mode`), and the ancestor-metadata fix to `isolate`.

## 8. Threats to validity

- **Statistical power.** At 6 runs a cell, and 12 discriminating runs per arm, only very large differences in pass rate are detectable. "Not supported" means no evidence of a gain at this size, not evidence that there is no gain.
- **Ceiling.** Cursor and FEAT were at the ceiling, which leaves Codex on BUG and CROSS as the only real test of correctness.
- **Task authorship.** Claude wrote the tasks, plants, reference patches and hidden tests. They are in this repository for review.
- **One repository, one language, cheap models.** The packs are written mainly for Claude Code and stronger models, and they may matter more or less elsewhere.
- **How the packs were installed.** They were installed as project files, not as plugins. Superpowers' hook text went into `AGENTS.md`, and pstack's models were pinned to the parent model. Each choice follows the vendor's own guidance for that CLI, but none is exactly the plugin experience.
- **Measurement gaps.**
  - Test-first misses edits made through shell commands (for example, `cat >` in Codex) and edits by pstack's subagents. It can only undercount.
  - It is not known whether Cursor's usage figures include pstack's subagent tokens, so pstack's cost may be a lower bound. It used subagents in only 10 tool calls.
  - Tests that bite were checked against both slips together, so a test that catches only one slip still counts as biting.

## 9. Conclusions

1. Installing a popular skill pack does not, on this evidence, make a cheap agent produce more correct changes on real tasks. Where the agent was already strong (Cursor) there was nothing to gain. Where it was not (Codex), Superpowers' perfect record is suggestive but not significant.
2. The packs reliably change process. Superpowers in particular produces test-first work and tests that detect the bug. pstack does so less often, and Pocock only when one of its skills is triggered.
3. That process costs about 2.3 to 2.8 times the tokens for Superpowers and pstack, and about 1.5 to 1.7 times for Pocock. The change itself stays the same size; the extra goes into tests and extra Maven runs.
4. The failures that did happen came from misunderstanding the system, and a test written from the same misunderstanding does not catch them. The hidden tests, which exercise the change end to end through the REST API, caught every one. "Test the behaviour the user described, through the interface they use" is a better target for a skill than "write the test first".
5. A pack whose skills are triggered only by description matching may simply not fire. Measure uptake before drawing conclusions about any skill.

## 10. Reproducing

1. Clone shopizer and check out `6a4a0a6`.
2. Run `scripts/build_arms.sh` to build the arms.
3. Run `scripts/localize.sh` to write `trial.local.toml` with your home folder.
4. Run `trialrig run trial.local.toml --out <dir>`.
5. Grade and analyse:
   - `scripts/bite.sh <dir>/runs bite.json` for tests that bite;
   - `python3 -I scripts/analyse.py <dir>/runs bite.json` for the tables in this report;
   - `scripts/reverify.sh` to regrade any single run from its saved diff.

Codex needs a clean home holding only `auth.json`, a `.gitconfig` and a link to `~/.m2`.

## Appendix: files

| Path | Contents |
| --- | --- |
| `results/stage1/runs/<task>/<arm>/<agent>/<rep>/` | `run.json` (tokens, tool calls, claim), `agent.diff`, `agent.numstat`, `verify-summary.json`, `raw.out.gz` (agent event log), `verify-mvn.log.gz`, and `bite-mvn.log.gz` (BUG only) |
| `results/runs.csv` | One row per run with every measure in this report |
| `results/analysis.md` | Full output of `analyse.py`, including per-cell detail |
| `results/report.md`, `results/plan.md` | The rig's report (with bootstrap intervals) and its stage-2 plan |
| `results/gate.md`, `results/calibration.md` | Checks made before the measured runs |
| `tasks/`, `hidden/` | Prompts, plants, reference patches and hidden tests |
| `arms/` | Placebo skill; the built packs are recreated by `build_arms.sh` |

Logs were scrubbed before publishing: home-folder paths, the username and the machine name are replaced. The credentials and tokens that appear in the logs are shopizer's own public test fixtures.
