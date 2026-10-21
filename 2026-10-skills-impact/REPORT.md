# Engineering report: do popular agent skill packs improve code changes?

| | |
| --- | --- |
| Experiment | `2026-10-skills-impact` |
| Date run | 2026-10-21 (stage 1, 162 runs; no stage 2) |
| Design | [README.md](README.md), written and frozen before any measured run, with an amendment log |
| Harness | [AgentTrialRig](https://github.com/meabs/AgentTrialRig) 0.6.1 |
| Raw data | [results/](results/) (unchanged since the run) |
| Revision | 2026-10-21, after an engineering-rigour review. The preregistered results (section 6) are unchanged. Everything the review added is in section 7 and labelled **retrospective** or **exploratory**. Section 8 lists the measurement defects found and their corrections. |

## 1. Summary

We gave two cheap coding agents three real change tasks in a Java e-commerce codebase. Each agent ran with no skills, a placebo skill, or one of three widely promoted skill packs (Superpowers, Matt Pocock's skills and Cursor's pstack). A hidden test suite, run after each agent finished, decided whether each change was correct.

- **Correctness: no gain was demonstrated, and the data cannot rule one out.**
  - Superpowers passed 24/24 runs on the two discriminating tasks, against 22/24 with no skills. The difference is +8 points, with a 95% interval of −7 to +26.
  - The comparison rests on one task and agent pair: the control failed only on Codex's CROSS runs. With three tasks, nothing here generalises to other tasks.
- **Process: the packs change how agents work.** The most robust result is from Superpowers.
  - Its runs edited a test file before production code in 31 of 36 runs, against 0 of 36 with no skills.
  - In 19 of 36 runs the logs show full test-driven development: a failing run of the new test, then the fix, then a passing run. Codex alone did this in 13 of 18 runs. The control never did.
- **Test quality is not clearly better.** On Codex, the control's tests already caught both planted defects in every bug run. The packs' advantage in "tests that bite" comes from Cursor, where the control rarely wrote tests at all. After correcting for multiple comparisons, the preregistered H4 result is not significant.
- **Cost: Superpowers and pstack use about 2.3 to 2.8 times the tokens; Pocock about 1.5 to 1.7 times.** Pack runs take more turns, run the tests more often and write more test code. The production change stays the same size. The logs do not show which of these the extra tokens pay for.
- **The failures came from misunderstanding the system.**
  - The 4 bug failures each fixed one of two causes. Their own tests, checked against each defect separately, caught only the defect they had fixed.
  - 6 of the 7 multi-file failures wrote no tests at all.

## 2. Question and approach

Skill packs are markdown instruction bundles that coding agents load on demand. The most visible ones promise better engineering discipline: test-driven development, systematic debugging, and "verify before you claim done". The question is whether they change outcomes that matter (correct changes, and at what cost) on a real repository.

The approach is a controlled trial:

- Each arm changes only the skills installed in the repository.
- Each task has a reference solution and a hidden test written in advance.
- Pass or fail is decided by running the full Maven build with the hidden tests added, never by what the agent says.
- Hypotheses, decision rules and sample sizes were fixed in the design before any measured run.

## 3. Test setup

### 3.1 Agents

| Agent | CLI | Model | Settings |
| --- | --- | --- | --- |
| Codex | `codex-cli 0.157.0` | `gpt-5.6-luna` | Reasoning effort high, `danger-full-access` sandbox (the rig's own sandbox applies) |
| Cursor | `cursor-agent 2026.10.19-6bbf2c4` | `grok-4.7-low` ("Grok 4.7 256K Low" in all 90 run logs) | Default settings; the cheapest Grok model in Cursor |

The design listed Cursor CLI 2026.10.01. The CLI updated itself to 2026.10.19 at 08:21 on the day of the run, before any measured Cursor run (the first started at 10:59). No later version is installed, so every measured run used 2026.10.19. Token totals are not compared between agents, because each CLI counts them differently.

### 3.2 Repository

[shopizer](https://github.com/shopizer-ecommerce/shopizer) at commit `6a4a0a6` is a Spring Boot Maven multi-module platform with about 1,200 Java files. It builds offline under JDK 21. The REST layer has full-stack integration tests (`TestRestTemplate` against H2), and the hidden tests reuse them. Three quirks of the codebase mattered:

- It has no bean-validation provider, so `@Pattern` and similar annotations never run.
- The manufacturer API turns every exception into a 503.
- Hibernate creates new columns itself.

### 3.3 Arms

| Arm | Source (pinned) | Installed as | Visible to the model |
| --- | --- | --- | --- |
| `none` | - | nothing | built-ins only |
| `placebo` | written for this experiment | `.agents/skills/careful-engineering/SKILL.md`: 514 words of generic advice with nothing on testing or verification | 1 skill |
| `superpowers` | `obra/superpowers` `b739a8a` | all 15 skills; the text its `sessionStart` hook injects is placed in `AGENTS.md` | 15, entry skill pre-loaded |
| `pocock` | `mattpocock/skills` `5beb35b` | the 27 skills in its plugin manifest | 11 (16 are `disable-model-invocation`) |
| `pstack` (Cursor only) | `cursor/plugins` `190d287`, pstack 0.15.29 | `.cursor/skills`, `.cursor/agents`, and a model rule setting every role to `inherit-parent`; each prompt is prefixed with `/poteto-mode` | `poteto-mode` pre-loaded; it reaches the other 55 skills by file path |

### 3.4 Isolation

Both CLIs load every skill in the user's home folder. To stop that leaking into the control:

- **Codex** runs with a clean `HOME` and `CODEX_HOME`.
- **Cursor**, which cannot log in under a clean home, runs with the rig's `isolate`, a `sandbox-exec` profile that denies the skill, plugin and agent folders.
- **Both** are denied this repository, which holds the hidden tests.

Two checks support the isolation:

- **A gate before the measured runs** ([results/gate.md](results/gate.md)) showed each arm seeing exactly the built-ins plus its own pack.
- **A retrospective search of the event logs** found no trace of any pack skill (skill names, skill folders or `SKILL.md` reads) in any of the 72 `none` and `placebo` runs.

### 3.5 How each pack reached the model (comparability)

The arms did not deliver their instructions the same way, and that shapes what each result means.

| Arm | Delivery | Consequence |
| --- | --- | --- |
| `placebo` | Discovered by its description | Read in 36/36 runs; its broad description always matched |
| `superpowers` | Bootstrap text always present (`AGENTS.md`), which then points the agent at the right skill | Read in 36/36 runs by construction |
| `pocock` | Discovered by each skill's description; 16 of 27 skills cannot be model-invoked | Read in 18/36 runs, almost all of them on BUG (section 7.5) |
| `pstack` | Invoked explicitly with `/poteto-mode`; every subagent role pinned to the parent model instead of the shipped `grok-4.7-xhigh-fast` and `claude-opus-5-5-xhigh` | Always active; not pstack as shipped, which would change the model under test |

Each arm therefore tests **the package as delivered here**, not the value of its individual instructions. Superpowers' always-on bootstrap gives it an advantage that a pack relying on discovery does not get. Pocock's result mostly reflects whether its skills triggered. pstack's result is for pstack without its stronger subagent models. A fair test of instructions alone needs the same delivery mechanism in every arm (section 11).

## 4. Tasks

Each prompt describes a symptom or a requirement as a merchant would, and never mentions skills, tests or tools.

| ID | Kind | What the agent had to do | Hidden test |
| --- | --- | --- | --- |
| `BUG` | Bug fix | Specials with an end date never show on the storefront. Two independent slips were planted behind one symptom: the product mapper stores the end date as the start date, and `ProductPriceUtils.finalPrice` checks the start date where it should check the end date | 5 API tests across date windows |
| `FEAT` | Feature | A per-store cart line limit read from merchant configuration (default 99), on every cart endpoint, without a restart; 400 and an unchanged cart when exceeded | 7 API tests |
| `CROSS` | Multi-file | An optional manufacturer `website`, stored, settable, and returned in detail, list and product JSON; anything not `http(s)://` gets 400 and nothing is stored | 5 API tests |

Each hidden test fails on the starting code and passes with `tasks/<id>/reference.patch`, and the full suite passes with each reference. Calibration ([results/calibration.md](results/calibration.md)) kept a task only if the control failed it at least once in 3 runs on one agent. FEAT never met that bar. It was kept for cost and process measures and excluded from the pass-rate tests before the run.

## 5. Metrics

| Metric | Definition |
| --- | --- |
| **Pass** | Maven ran the whole reactor; every hidden test ran (full count, none skipped) and passed; no other test failed, including tests the agent added (`verify.sh` and `summarize.py`) |
| **Overclaim** | The agent's final `VERIFICATION` line says `passed` but the run fails |
| **Test-file-first** (preregistered as "test-first", H5) | The first edit under `src/test` comes before the first under `src/main`, counting only edits made through the agent's edit tool. It says nothing about whether a test was run |
| **Confirmed TDD** (retrospective) | From the full event log: a test file was edited before any production file; a test run in between failed with a test failure in a class the run changed (not a compile error); and a test run after the first production edit passed. Runs whose logs cannot settle this (a subagent, an unreadable shell edit, or test output that does not name the failing class) are **unknown**, not false |
| **Bites** (preregistered, H4) | The run's test changes, applied to the code with both defects, fail |
| **Catches both defects** (retrospective) | The run's tests are run on four versions of the code: both defects, price defect only, mapper defect only, and both fixed. A test case counts only if it passes on the fixed code. The run catches both defects if some valid case fails on each single-defect version. Compile errors are "not executable", never detection |
| **Skill read** | The event log shows a read of a `SKILL.md` |
| **Tokens** | Total tokens as each CLI reports them, split into fresh input, cached input and output. Codex counts cached input inside input; Cursor counts it separately |
| **Estimated $** | Tokens at list prices (section 7.6). Not a billed amount |
| **Maven test runs** | Shell commands that ran Maven with a test, verify, install or package goal and without `-DskipTests` |
| **Production / test lines** | Lines added plus removed in the final diff outside and inside `src/test` |

## 6. Preregistered results (unchanged)

### 6.1 Execution

| | Codex | Cursor |
| --- | --- | --- |
| Runs | 72 (3 tasks × 4 arms × 6) | 90 (3 tasks × 5 arms × 6) |
| Wall time | 1 h 35 min | 1 h 40 min |
| Crashes, timeouts, infrastructure reruns | 0 | 0 |

### 6.2 Pass rate

| Task | Agent | `none` | `placebo` | `superpowers` | `pocock` | `pstack` |
| --- | --- | --- | --- | --- | --- | --- |
| BUG | Codex | 6/6 | 4/6 | 6/6 | 5/6 | - |
| BUG | Cursor | 6/6 | 6/6 | 6/6 | 5/6 | 6/6 |
| CROSS | Codex | 4/6 | 4/6 | 6/6 | 4/6 | - |
| CROSS | Cursor | 6/6 | 6/6 | 6/6 | 5/6 | 6/6 |
| FEAT | Codex | 6/6 | 6/6 | 6/6 | 6/6 | - |
| FEAT | Cursor | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |

### 6.3 Hypotheses

The p-values are one-sided Fisher exact tests against `none`, as preregistered. The difference with a 95% interval and the Holm-adjusted p (across the nine tests) were added by the review.

| # | Claim | Pack | `none` | Difference (95% CI) | p | Holm p | Preregistered verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | Superpowers raises the pass rate (BUG + CROSS) | 24/24 | 22/24 | +8 pts (−7 to +26) | 0.245 | 0.979 | not supported |
| H2 | Pocock raises the pass rate (BUG + CROSS) | 19/24 | 22/24 | −12 pts (−33 to +9) | 0.951 | 1.000 | not supported |
| H7 | pstack raises the pass rate (Cursor) | 18/18 | 18/18 | 0 (−18 to +18) | 1.000 | 1.000 | not testable (ceiling) |
| H4 | Superpowers' BUG tests bite | 12/12 | 8/12 | +33 pts (+2 to +61) | 0.047 | 0.280 | supported at α = 0.05 |
| H4 | Pocock's BUG tests bite | 12/12 | 8/12 | +33 pts (+2 to +61) | 0.047 | 0.280 | supported at α = 0.05 |
| H4 | pstack's BUG tests bite | 5/6 | 8/12 | +17 pts (−28 to +47) | 0.439 | 1.000 | not supported |
| H5 | Superpowers is test-file-first | 31/36 | 0/36 | +86 pts (+68 to +94) | < 0.001 | < 0.001 | supported |
| H5 | Pocock is test-file-first | 10/36 | 0/36 | +28 pts (+12 to +44) | < 0.001 | 0.004 | supported |
| H5 | pstack is test-file-first | 6/18 | 0/18 | +33 pts (+9 to +56) | 0.010 | 0.067 | supported at α = 0.05 |
| H6 | Fewer overclaims (descriptive) | Superpowers 0, pstack 0, Pocock 4 | 2 | - | - | - | see 7.7 |

The design did not specify a multiple-comparison correction. The preregistered verdicts are kept as written. With Holm's correction, H4 (both packs) and pstack's H5 no longer reach 0.05; H5 for Superpowers and Pocock does. The placebo passed 20/24 and was test-file-first in 0/36 runs.

## 7. Retrospective review

### 7.1 Grading audit

- **Independent regrade.** Every run was regraded from its Maven log alone, by a parser written separately from `summarize.py` (`scripts/audit.py`). It agrees with the recorded grade on **162/162** runs.
- **Hidden suites.** Every hidden suite ran its full count (5, 7 and 5 tests) with nothing skipped, in 162/162 runs.
- **Weaknesses found.** `summarize.py` had three that could have produced a false pass (section 8). The audit shows none of them affected any recorded grade.

### 7.2 Where the pass-rate evidence comes from

The 6 runs in a cell repeat one task. For generalising to other tasks the independent units are the 3 tasks (6 task-and-agent cells), not the 162 runs.

- **Ceiling.** `none` passed every run in 5 of the 6 cells. The only cell where the control failed is Codex on CROSS (4/6), so every pass-rate gain any pack could show had to come from there.
- **That one cell.** In it, Superpowers passed 6/6, a difference of +33 points (−12 to +70, p = 0.23), while the placebo and Pocock each passed 4/6. Restricted to Codex on BUG and CROSS (exploratory), Superpowers is 12/12 against 10/12, a difference of +17 points (−10 to +45).
- **What the intervals mean.** They include zero, so no gain is demonstrated. They also include gains of 25 points or more, so the data do not show "no effect" either. The study was not sized to tell these apart.

### 7.3 Tests that catch each defect (BUG)

The original measure counted a test as biting if it failed on code that had both defects. A test that caught only one of them still counted. The retrospective harness (`scripts/mutation.py`) runs each run's tests on four versions of the code (section 5). As a control, the hidden test went through the same harness and caught each defect on its own.

| Agent | Arm | Both defects | One defect only | None caught | No tests |
| --- | --- | --- | --- | --- | --- |
| Codex | none | 6 | 0 | 0 | 0 |
| Codex | placebo | 4 | 2 | 0 | 0 |
| Codex | superpowers | 6 | 0 | 0 | 0 |
| Codex | pocock | 5 | 1 | 0 | 0 |
| Cursor | none | 0 | 2 | 0 | 4 |
| Cursor | placebo | 0 | 1 | 0 | 5 |
| Cursor | superpowers | 5 | 1 | 0 | 0 |
| Cursor | pocock | 3 | 3 | 0 | 0 |
| Cursor | pstack | 5 | 0 | 0 | 1 |

What this adds:

- **No test was useless.** Every test written caught at least one defect, and none was unexecutable or failed on the fixed code.
- **Coverage differs by agent.**
  - On Codex, the control's tests caught both defects in 6/6 runs, the same as Superpowers.
  - On Cursor, the control wrote tests in only 2 runs, each catching one defect, against 5/6 runs catching both with Superpowers and pstack.
  - So the pooled advantage (exploratory: Superpowers 11/12 against 6/12) comes entirely from Cursor writing tests at all.
- **Each failed BUG run's tests caught only the defect that run fixed.** That held for all 4 failures (three caught only the price defect and one only the mapper defect), so their passing tests could not reveal the half they had missed.

### 7.4 Test-file-first and confirmed TDD

| Agent | Arm | Test-file-first (H5) | Confirmed TDD | Test file first, cycle not shown | Production first | No test edits | Unknown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Codex | none | 0/18 | 0 | 0 | 8 | 10 | 0 |
| Codex | placebo | 0/18 | 0 | 0 | 9 | 9 | 0 |
| Codex | superpowers | 17/18 | 13 | 4 | 0 | 0 | 1 |
| Codex | pocock | 7/18 | 6 | 0 | 6 | 5 | 1 |
| Cursor | none | 0/18 | 0 | 0 | 2 | 16 | 0 |
| Cursor | placebo | 0/18 | 0 | 0 | 2 | 16 | 0 |
| Cursor | superpowers | 14/18 | 6 | 6 | 4 | 0 | 2 |
| Cursor | pocock | 3/18 | 1 | 2 | 6 | 9 | 0 |
| Cursor | pstack | 6/18 | 4 | 0 | 3 | 4 | 7 |

What the logs show:

- **Superpowers.** Of its runs that edited a test file first but are not confirmed, across both agents, 9 met only a compile error before the fix: the test called code that did not exist yet. That is a common TDD style, but it is not a failing test. 3 more runs are unknown because the test output does not name the failing class.
- **pstack.** 7 of its 18 runs are unknown, mostly because a subagent did part of the work out of sight of the main log.
- **Agreement with H5.** The edit-order measure (H5) and the new extractor agree exactly on test-file-first (0 differences).
- **Exploratory comparison.** Confirmed TDD was 19/36 for Superpowers, 7/36 for Pocock and 4/18 for pstack, against 0 for `none` and the placebo.

### 7.5 Did Pocock's skills run?

| Task | Codex: read / passed | Cursor: read / passed |
| --- | --- | --- |
| BUG | 6/6 read; 5 of those passed | 6/6 read; 5 of those passed |
| CROSS | 0/6 read | 1/6 read |
| FEAT | 1/6 read | 4/6 read |

Pocock's skills fire by description matching. A bug report matched `diagnosing-bugs`, but feature and multi-file requests rarely matched anything. H2 is therefore a test of the pack as installed. On CROSS and FEAT it says almost nothing about Pocock's instructions, because they were mostly never read. Comparing runs that read a skill with runs that did not is confounded with the task, so it is not used as evidence.

### 7.6 Cost and effort

Two relative-cost figures had been published, using different methods:

- **`report.md` (the rig):** each run's tokens divided by the `none` *mean* for the same task and agent, then averaged.
- **`analysis.md`:** the *median* of each run's tokens divided by the `none` median.

The mean method gives lower numbers when a few control runs are expensive. Both are shown here; the summary quotes the range.

| Agent | Arm | Mean tokens (fresh / cached / output) | Relative, mean method | Relative, median method | Est. $ (all runs) | Passes | Est. $ per pass | Median s | Median Maven test runs | Median production / test lines |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Codex | none | 2.17M (0.10M / 2.06M / 12k) | 1.00 | 1.00 | 1.37 | 16 | 0.09 | 134 | 2 | 50 / 0 |
| Codex | placebo | 2.56M (0.11M / 2.44M / 13k) | 1.16 | 1.25 | 1.57 | 14 | 0.11 | 161 | 1 | 46 / 25 |
| Codex | superpowers | 5.86M (0.20M / 5.65M / 19k) | 2.62 | 2.77 | 3.15 | 18 | 0.18 | 307 | 7 | 44 / 128 |
| Codex | pocock | 2.97M (0.12M / 2.84M / 14k) | 1.41 | 1.74 | 1.76 | 15 | 0.12 | 192 | 4 | 42 / 74 |
| Cursor | none | 0.52M (0.06M / 0.45M / 9k) | 1.00 | 1.00 | 19.29 | 18 | 1.07 | 118 | 0 | 50 / 0 |
| Cursor | placebo | 0.49M (0.07M / 0.41M / 8k) | 0.96 | 1.05 | 18.18 | 18 | 1.01 | 116 | 0 | 41 / 0 |
| Cursor | superpowers | 0.98M (0.09M / 0.88M / 11k) | 1.93 | 2.33 | 35.87 | 18 | 1.99 | 170 | 2 | 51 / 74 |
| Cursor | pocock | 0.66M (0.08M / 0.57M / 9k) | 1.33 | 1.49 | 24.53 | 16 | 1.53 | 149 | 0 | 38 / 20 |
| Cursor | pstack | 1.18M (0.12M / 1.05M / 14k) | 2.38 | 2.75 | 43.56 | 18 | 2.42 | 206 | 2 | 44 / 38 |

Reading the cost table:

- **Prices.** The dollar figures are estimates at list prices: Codex $0.20, $0.02 and $1.20 per million fresh-input, cached-input and output tokens. Cursor is priced at $2 per million for all input including cache reads (the design's rule, an upper bound) and $6 per million for output. At typical cached-input rates of $0.20 to $0.50 per million, Cursor's total of $141 would be $33 to $51. The billed amount is on Cursor's dashboard and is not reported here.
- **Cost per pass.** With most cells at the ceiling, cost per verified pass mostly restates relative cost, so it is not a measure of value.
- **Where the extra tokens go.** Pack runs make more turns and more Maven test runs, and they add test code. The production change stays the same size. Most tokens are context re-sent on every turn, so the logs cannot divide the extra tokens among those causes.

### 7.7 Overclaims

Codex said `passed` in 70 of 72 runs whatever happened, so on Codex the overclaim count equals the failure count: 2 for `none`, 3 for the placebo, 3 for Pocock and 0 for Superpowers. Superpowers' zero reflects its zero failures, not more honest reporting.

On Cursor the packs did change behaviour:

- With no skills, Cursor usually compiled and stopped (median 0 Maven test runs) and said `not-run` in 13 of 18 runs.
- With Superpowers it ran the tests (median 2 runs) and reported `passed` in 18 of 18 runs.

### 7.8 Failure analysis

Each of the 11 failures was read in its diff and Maven log, and none was an infrastructure fault.

| Failure | Runs | What happened |
| --- | --- | --- |
| Half a fix | 4 BUG runs: Codex placebo ×2, Codex pocock, Cursor pocock | Fixed one of the two causes. Each wrote tests, which caught only the cause it fixed (7.3). All 4 claimed `passed` |
| Validation that never runs | 5 CROSS runs: Codex none ×2, Codex placebo, Codex pocock, Cursor pocock | Used an annotation that nothing evaluates, or put the check inside the `try` that converts errors to 503. None of the 5 wrote a test |
| Validation that broke the API | 2 CROSS runs: Codex placebo, Codex pocock | Added `spring-boot-starter-validation`, which switched on validation for every endpoint and broke existing tests. 1 of the 2 wrote a test |

On Codex CROSS, runs that wrote any test passed 11 of 12 times, and runs that did not passed 7 of 12. This is exploratory and confounded, because Superpowers runs always wrote tests. It is consistent with testing helping on the task where the control could fail, but it does not show that.

## 8. Measurement defects found and corrected

| # | Defect | Effect | Correction |
| --- | --- | --- | --- |
| 1 | `summarize.py` did not check the number of hidden tests, skipped hidden tests, or unreadable reports | Could pass a run whose hidden tests did not all run | Fixed: each of these now fails the run, with regression tests. The audit found no affected run, so no grade changed |
| 2 | "Tests that bite" ran against both defects at once | Could not tell whether a test caught both defects | Per-defect mutation analysis added (7.3); original H4 kept |
| 3 | "Test-first" measured edit order only, ignored shell edits and subagents, and was reported as if it showed TDD | Overstated what was observed | Renamed test-file-first; confirmed TDD added, with "unknown" for insufficient evidence (7.4) |
| 4 | The first report said the extra tokens "go into tests and extra Maven runs" | Attribution the logs cannot support | Corrected (7.6) |
| 5 | The first report said each failure wrote tests that matched its wrong model | True for the 4 BUG failures only; 6 of 7 CROSS failures wrote no tests | Corrected (7.8) |
| 6 | Two relative-cost methods were quoted without saying so | Figures disagreed (2.62 against 2.77, for example) | Both shown and defined (7.6) |
| 7 | No adjustment for nine hypothesis tests | H4 looked significant | Holm-adjusted p-values added alongside (6.3) |
| 8 | "Maven runs" counted any Maven command, including compiles | Inflated test effort | Replaced by Maven test runs (section 5) |
| 9 | The export scrubbed home paths but not the username and host name inside compressed logs | Personal names in published logs | Export fixed, and logs re-scrubbed (earlier commits still hold them, which the owner accepted) |

Three parser bugs were caught by spot checks while building the retrospective tools, and fixed before their results were used:

- ANSI colour codes hid Codex's failing-test lines.
- A quote before `mvn` hid Codex's test runs.
- The new table had a malformed separator.

## 9. Threats to validity

- **Too few tasks.** Three tasks, two at the ceiling, cannot support claims about tasks in general.
- **Power.** The pass-rate intervals are wide (about ±25 points).
- **Unequal delivery.** The arms did not reach the model the same way (3.5), so a result belongs to a package and its delivery, not to its instructions.
- **Task authorship.** Claude wrote the tasks, plants, reference patches and hidden tests. Planted bugs are not real bugs.
- **One repository, one language, cheap models.** The packs are written mainly for Claude Code and stronger models.
- **Logs.** Confirmed TDD depends on what the logs record; pstack's subagents and some test output leave runs unknown.
- **Pre-registration.** The retrospective measures were defined after seeing the data. They are labelled as such and do not replace the preregistered tests.

## 10. Conclusions, and whether the original ones stand

| Original conclusion | Status after review |
| --- | --- |
| No pack measurably raised correctness | **Stands.** The intervals include gains of about 25 points, so "no gain was demonstrated" is the accurate wording, not "packs do not help" |
| The packs reliably change process (Superpowers test-first) | **Stands, and is better supported.** Confirmed TDD in 19/36 Superpowers runs against 0/36 for the control |
| Superpowers produces tests that detect the bug | **Weakened.** On Codex the control's tests were as good. The advantage is Cursor writing tests at all, and H4 is not significant after correction |
| The process costs 2 to 3 times the tokens; the extra goes into tests and Maven runs | **The cost ratio stands. The attribution is withdrawn** |
| Failures came from wrong models of the system, which tests encoding that model cannot catch | **Narrowed.** True of the bug failures; the multi-file failures mostly had no tests |
| Testing the described behaviour through the real interface is a better target than "write the test first" | **A hypothesis, not a finding.** It motivates the next experiment |
| Measure skill uptake before judging a skill | **Stands** |

## 11. Proposed next experiment (not run here)

**Question:** can one short instruction, "verify the behaviour the user described end to end, through the interface they use, before finishing", match or beat a comprehensive pack?

Design:

- **Arms:** `none`; a placebo of the same length; `targeted` (the one instruction); `superpowers`.
- **Same delivery for every arm:** each is a single always-loaded `AGENTS.md` block of similar length, with Superpowers' skills discoverable as usual. This separates the instructions from how they arrive.
- **Tasks:** many different tasks, at least 16, with 1 or 2 runs each. They should come from more than one repository and include real historical bugs where possible, not only planted ones.
- **Acceptance tests:** independent and API-level, written or reviewed by someone other than the task author, and checked against a reference solution.
- **Model:** one agent and model throughout (Codex with `gpt-5.6-luna`).
- **Analysis:** the task is the unit, with a paired per-task permutation test and Holm correction. Confirmed TDD and per-defect test coverage go in as secondary measures.

The many-task part of this has started as a separate experiment: [2026-10-skills-tasks](../2026-10-skills-tasks/), with the same four arms as this one, on Codex. No new runs are added to this dataset.

## 12. Reproducing

From this folder:

```
scripts/reproduce.sh
```

It rebuilds `analysis.md`, `runs.csv` and `results/retro/{process,audit}.json`, plus `analysis-retro.md`, from the committed raw runs, then runs the 42 grading regression tests in `tests/`. Running it on the committed data reproduces the committed files exactly.

The steps that need Maven and the shopizer clone are:

- `scripts/mutation.py` (about 40 minutes);
- `scripts/reverify.sh <out> <task> <arm> <agent> <rep>`, which regrades one run from its saved diff;
- the full trial: `scripts/build_arms.sh`, `scripts/localize.sh`, then `trialrig run trial.local.toml`.

## Appendix: files

| Path | Contents |
| --- | --- |
| `results/stage1/runs/<task>/<arm>/<agent>/<rep>/` | Raw runs: `run.json`, `agent.diff`, `agent.numstat`, `verify-summary.json`, `raw.out.gz`, `verify-mvn.log.gz`, `bite-mvn.log.gz` |
| `results/analysis.md`, `results/runs.csv` | Preregistered analysis (`analyse.py`) |
| `results/report.md`, `results/plan.md` | The rig's report and stage-2 plan |
| `results/retro/` | Retrospective: `analysis-retro.md`, `mutation.json` and `mutation-logs/`, `process.json`, `audit.json` |
| `results/gate.md`, `results/calibration.md` | Checks made before the measured runs |
| `scripts/` | Grading (`verify.sh`, `summarize.py`), analysis (`analyse.py`, `retro.py`, `stats.py`, `process.py`, `mutation.py`, `audit.py`) and `reproduce.sh` |
| `tests/test_grading.py` | Regression tests for grading and analysis |
| `tasks/`, `hidden/`, `arms/` | Tasks, hidden tests, arms |

Published logs have home paths, the username and the machine name replaced. The credentials in the logs are shopizer's public test fixtures.
