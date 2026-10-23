# Elephant-Goldfish Model on a feature task: pilot report (Codex)

Run on 2026-10-23. **A pilot, not an experiment.** It checks whether EGM can be run and graded at scale, and what it costs. Two EGM runs and four baseline runs are too few to say whether EGM helps. The design is in [README.md](README.md).

## Claude acted as the human approver, to make the experiment scalable

EGM expects a person to approve every drafted section and every review stage. A full trial needs 60 or more EGM runs, too many for a person to sit through. So in this pilot **Claude (the assistant running these experiments) acted as the human approver**, following a fixed rule that a script or a model could apply in a full trial:

- requirements come only from the task text. Claude knows the hidden tests, so it added no requirement of its own;
- a section is approved unless it contradicts the task text;
- in the review, the approver proceeds at stages 5, 6 and 8, and at stages 7 and 9 it has the agent resolve the findings, then accepts the proposed fixes unless one contradicts the task text.

Every message Claude sent is saved in `results/egmN/turns/NN.in.md` and listed below. The rule was extended once during the pilot; see "What changed from the design".

This is the pilot's main limit: it tests EGM **without a human's judgement**. A real engineer brings knowledge the task text does not contain, and that may be where much of EGM's value lies.

## Summary

- **The first feature was too easy.** On LOWSTOCK (a low-stock report with a fully specified API), plain Codex at low effort passed all 9 hidden tests in both baseline runs, in under a minute. A spec process cannot improve on that, so it was replaced before any EGM run.
- **The second feature is hard.** DISCOUNT asks for merchant-managed discount codes that replace a hard-coded rule. It touches persistence, an admin API, validation, cart totals, category hierarchy and the existing promo pipeline. The reference implementation changes 7 files, adding about 440 lines across 4 modules. Plain Codex at low effort passed 4 and 2 of its 16 hidden tests.
- **EGM produced thorough designs, but the code built from them was no better.**

  | run | hidden tests passed | tokens | cost | time | approver messages |
  | --- | --- | --- | --- | --- | --- |
  | baseline 1 (task only) | 4/16 | 0.76M | $0.032 | 91 s | 0 |
  | baseline 2 (task only) | 2/16 | 0.76M | $0.030 | 62 s | 0 |
  | EGM 1 | 3/16 | 7.90M | $0.294 | 550 s | 15 (+ start, build) |
  | EGM 2 | 1/16 | 5.47M | $0.216 | 419 s | 17 (+ start, build) |

  No existing test broke in any run.
- **The reviews found real problems.** The Goldfish reviewers flagged things the reference implementation also had to deal with:
  - the old Drools rule and the one-day expiry of applied codes;
  - an existing per-item promo calculator that cannot apply a fixed amount capped at the cart level;
  - existing category-lineage services to reuse;
  - in run 1, the draft's plan for migration files in a project whose schema comes from Hibernate.

  The final designs ran to 405 and 132 lines and named the files to change.
- **The build is where it failed.** As EGM describes, a fresh coding session (low effort, like the baselines) was given only the approved design. Both times it wrote a skeleton and stopped:
  - run 1: 82 lines of code (an entity, a repository, a 10-line controller);
  - run 2: 81 lines of code (an entity, a service, removal of the Drools rule).

  Neither touched the cart totals, the category rules or most of the validation. Both said they had finished and that the project compiled. The spec's quality did not carry over into the code.
- **With a Claude approver using judgement, both EGM and a plain plan-first process beat plain Codex, and EGM did no better than plan-first** (follow-up 2 below). EGM + approver passed 16, 5 and 16 of 16 hidden tests; plan + approver 6, 13 and 16. EGM cost about five times as much. What decided the score was whether the approver made the design name the totals line `"discount"`. No Goldfish reviewer ever raised it.
- **With the build at medium effort, EGM did no better than plain Codex at medium effort** (follow-up 1 below). Both approved designs, built at medium effort, scored 4/16, as did plain Codex at medium effort with the task alone (4/16 twice). All four runs named the cart's discount line `order.total.discount` instead of the `discount` the task asks for, which fails every test that checks the amount. A diagnostic that accepts either name gives **13/16 for all four runs**, with the same three failures. Plain Codex cost about a quarter as much: $0.10 a run on average, against $0.43 for EGM.
- **EGM's review did not run as specified until corrected.** In both runs, Codex at low effort first spawned its reviewers with `fork_turns: "all"`, which copies the whole conversation into each one, so they were not Goldfish. It also merged review stages. After one correction from the approver (below), every later reviewer was spawned with fresh context (`fork_turns: "none"`), and each stage stopped at its own checkpoint. Run 2 still ran one combined critic at stage 7 instead of EGM's three.

## Follow-up 1: the build at medium effort

Run on 2026-10-23 after the pilot, at the user's request to fix the build step and test the fix. The two designs already approved in EGM runs 1 and 2 were each put into a fresh clone (`egm_drive.sh seed`). A fresh Codex session at **medium effort** was given the same build prompt ([arms/egm-build.md](arms/egm-build.md)). Nothing in the designs or the prompt changed. As the fair rival, plain Codex at medium effort got the task alone, twice, through the rig ([trial-medium-discount.toml](trial-medium-discount.toml)).

| run | hidden tests passed | diagnostic (either line name) | build cost | whole run cost | build time | lines added |
| --- | --- | --- | --- | --- | --- | --- |
| baseline medium 1 (task only) | 4/16 | 13/16 | — | $0.080 | 142 s | — |
| baseline medium 2 (task only) | 4/16 | 13/16 | — | $0.128 | 224 s | — |
| EGM 1, medium build | 4/16 | 13/16 | $0.296 | $0.573 | 4311 s* | 654 |
| EGM 2, medium build | 4/16 | 13/16 | $0.091 | $0.286 | 160 s | 596 |

The whole-run cost of an EGM run is its design and review (run 1: $0.277; run 2: $0.195) plus the build. No existing test broke in any run. Each build was a single session at `effort: medium`, checked in its session file.

\* EGM 1's build stalled seven times for about 576 seconds each, waiting for a model response; two of these are logged as reconnects after `max_output_tokens`. Its working time was about 5 minutes.

- **The build step is fixed.** At medium effort the builds wrote the whole feature: about 600 to 650 lines across 19 to 21 files, including the cart totals, category rules and validation that the low-effort builds left out.
- **One naming miss hides most of the work.** The task says the cart shows "a line in "totals" with code "discount"". Every medium run, EGM or not, used shopizer's existing constant `order.total.discount` instead. Neither EGM design, nor any of its review reports, names the line's code. The tests that check a discount amount all fail on this.
- **The diagnostic.** To see how much of the feature works apart from that miss, every run's diff was retested with the hidden test changed in one line, so that a line coded `order.total.discount` also counts ([scripts/diag_line_name.sh](scripts/diag_line_name.sh), results in `results/diagnostic-line-name/`). It is not the score; the score is the task as written.
  - All four medium runs pass 13/16 and fail the same three tests: a duplicate code is not answered with 409, an invalid code is not answered with 400 (500 instead), and a code is not shown as the merchant wrote it.
  - The reference still passes 16/16. The low-effort runs: baseline 11/16 and 2/16, EGM 3/16 and 1/16. Two low runs lose a test under the diagnostic, because the old Test1234 rule still produced an `order.total.discount` line, which the official test did not see.
- **So on this task, at this sample size, EGM added cost and nothing measurable.** The spec and its reviews did not pin down the one requirement every run missed. It also did not fix the three error-handling gaps that plain Codex at medium effort also left.

## Follow-up 2: a Claude approver using judgement

Run on 2026-10-23, at the user's request. The design (README, "Follow-up 2") was committed before any run (42765b6).

- **The approver.** Each run got a fresh Claude agent (Opus 5.5) that had never seen the hidden tests or the reference. It was given the brief ([arms/approver-brief.md](arms/approver-brief.md)) and the agent's messages, and replied as the engineer who asked for the feature. Its replies went to the agent verbatim. Each run's `approver-log.md` shows everything the approver was given, every tool call it made and every reply.
- **Arms.** In the EGM arm it approved EGM's drafting and all five review stages. In the plan arm it reviewed a plain Codex design. In both arms a fresh Codex session built from the approved design. Codex ran at medium effort in every session.

| run | hidden tests passed | diagnostic (either line name) | approved design names the line `"discount"` | approver replies | Codex cost | Codex time |
| --- | --- | --- | --- | --- | --- | --- |
| EGM + approver 1 | **16/16** | 16/16 | yes | 20 | $1.453 | 1693 s |
| EGM + approver 2 | 5/16 | 15/16 | no (says `OT_DISCOUNT_TITLE`) | 11 | $0.542 | 731 s |
| EGM + approver 3 | **16/16** | 16/16 | yes | 12 | $0.852 | 1170 s |
| plan + approver 1 | 6/16 | 16/16 | not mentioned | 3 | $0.148 | 291 s |
| plan + approver 2 | 13/16 | 13/16 | yes | 4 | $0.225 | 380 s |
| plan + approver 3 | **16/16** | 16/16 | yes | 4 | $0.202 | 376 s |
| plain medium (follow-up 1) | 4/16, 4/16 | 13/16, 13/16 | — | 0 | $0.080, $0.128 | 142 s, 224 s |

No existing test broke in any run. Codex cost covers every Codex session in the run (the draft, each reviewer and the build), from the session files. The approver's own Claude usage is not included.

- **An approver who uses judgement helps a lot, whichever process it reviews.**
  - Both approver arms beat plain Codex at the same effort. Plain Codex scored 4/16 twice, and no plain Codex run had ever passed all 16 tests on DISCOUNT. With an approver, three runs passed all 16: two EGM, one plan.
  - On the diagnostic, all six approver runs scored 13 to 16, against 13 for plain Codex. So the approver mainly fixed the one interface detail every earlier run missed. In four runs it also got the error handling right: duplicate codes answered with 409, invalid input with 400, and the code shown as the merchant wrote it.
- **The strict score follows one sentence in the design.** Every run whose approved design named the totals line `"discount"` scored 13 or 16. The two that did not scored 5 and 6, and 15 and 16 on the diagnostic.
  - In every run, the line name came from the approver, never from a Goldfish reviewer. The plan arm has no Goldfish, and in the EGM runs no review report raises it. Run 3's comprehension report mentions it only in the agent's proposed fix, after the approver had raised it.
  - EGM 2's approver asked for a `"discount"` line early on. At the last gate it then told the agent to use `Constants.OT_DISCOUNT_TITLE`, wrongly believing that constant is `"discount"`, and the build followed it.
  - Plan 1's approver never raised the line name.
- **EGM added no measurable gain over plan-first, at about five times the cost.**
  - Mean score: EGM 12.3 against plan 11.7, and 15.7 against 15.0 on the diagnostic. With three runs per arm, that difference means nothing.
  - EGM cost $0.95 of Codex per run on average against $0.19, took three times as long, and needed three to five times as many approver replies.
  - EGM's review did run as specified this time. Every Goldfish was spawned with `fork_turns: "none"`, so the pilot's method correction was never needed. EGM 1's approver asked for stages 5 and 6 to be rerun several times: 17 reviewer threads and $1.45.
- **The approvers stayed inside their clone.** Every tool call they made was a read inside their own run's clone, and none changed a file (`results/<run>/approver-audit.md`, from [scripts/audit_approver.py](scripts/audit_approver.py)). They never saw the hidden tests: those enter the clone only at grading, after approval.

**What Claude, running the experiment, added beyond relaying.** These additions are all in the saved messages:

- The fixed starts and the EGM review start, as designed.
- One sentence when the first review result reached each EGM approver, saying that fresh reviewers were now reviewing the approved draft.
- One procedural note to EGM 3's approver, which had approved after stage 5: stages 6 to 9 were still to come. Its reply was sent on as usual.

Neither addition said anything about requirements.

**Problems.**

- **The disk filled up during the diagnostics.** It was down to 567 MB free, mostly with files not belonging to these experiments. That broke two diagnostic runs, which were rerun. No grade or build was affected; their logs have no disk errors.
- To make room, I deleted the four follow-up 1 clones (already exported) and my own clean clone.
- The shared `~/.m2` shopizer jars are still clean after these runs.

## What a full trial would cost

- **EGM run:** about $0.22 to $0.29 and 7 to 9 minutes at low effort, plus about 17 approver messages. That is within the earlier estimate of $0.25 to $1.00. About $0.06 of run 1 went on the discarded first review.
- **60 EGM runs:** about $15 to $20; with baseline, plan-first and medium-effort arms, about $25 to $35 in all.
- **The approver:**
  - the approval rule is mechanical: approve, proceed, resolve, then auto accept;
  - the one judgement it needed, catching full-context reviewers, came from the session audit, which a script can do.

  So a scripted approver is feasible.
- **The tasks are the expensive part.** DISCOUNT took several hours to build: the prompt, 16 hidden tests and a reference implementation, each checked against the original code and the whole suite. A trial would need 10 or more such features.

## What the pilot changes for a full design

1. **Build at medium effort.** With a low-effort build, EGM's output is limited by how much code the build writes, not by the spec. The follow-up shows a medium-effort build writes the whole feature. A full trial should compare EGM with plain Codex at the same effort, which here matched it.
1. **Score near misses as well.** A single interface detail (the totals line's name) turned 13/16 into 4/16 in every medium run. A full trial should report a diagnostic score alongside the strict one, decided before the runs.
2. **Turn on Codex's subagents explicitly** (`--enable multi_agent_v2`). Without it, Codex 0.157 offers no spawn tool and EGM cannot run its review.
3. **Audit every review automatically** from the session files: each subagent's `fork_turns`, its parent, and its tokens. Subagent tokens are not in the main event stream; they are only in the session files.
4. **Count each arm's fair rival.** To isolate EGM's effect, the arms should include the task alone at the same effort as the build, a plan-first arm without reviewers, and medium effort, which has been the only clear gain in earlier experiments.

## Problems found along the way

- **Shared Maven repository.** Twice, the shared `~/.m2` received modified shopizer jars:
  - once from my own `mvn install` while building the reference implementation;
  - once from EGM run 2's build agent, whose design told it to run `./mvnw -DskipTests install`.

  A third time, in the follow-up, baseline medium run 2 ran `mvn -q -DskipTests install`. The rig, unlike the EGM driver, does not forbid this. The jars were rebuilt from the original code again and checked. The other runs going at the time all built from source (`-am` or the whole project), so none used them. EGM 2's medium build also tried `./mvnw -DskipTests install`, and the driver's sandbox stopped it.

  Grading is not affected, because the grader builds the whole project from source. But a later agent building only `sm-shop` would have used another run's code. Both times, the jars were rebuilt from the original code and checked. The driver's sandbox now forbids writes to the shopizer folder in `~/.m2`.

  Earlier experiments ran agents with the same shared repository; whether any of their agents ran `install` has not been checked.
- **shopizer quirks found while writing the tests:**
  - adding a second inventory entry to a product throws a null pointer, so LOWSTOCK's multi-entry test was dropped;
  - a category's parent is ignored unless both its id and its code are given, so the hidden test gives both.
- **A hidden-test assumption, loosened.** Run 2's design specified a paginated list for `GET /api/v1/private/discounts`. The task does not fix the list's shape, and the test expected a plain array, so the test now accepts either. This changed no result: run 2 built no discount API at all. The updated tests still pass 16 of 16 on the reference.

## Checks on the runs

- **Subagents.** Every Goldfish after the correction has its own session file, with its parent thread, depth 1, and `fork_turns: "none"` in the parent's spawn call. Audits: `results/egmN/audit.md`, from `scripts/audit_sessions.py`.
- **The skills were really used.** In both runs, the agent invoked `egm:egm-draft` and `egm:egm-review` by name, read the draft skill's reference files, and wrote EGM's reports (`results/egmN/design/`).
- **No run saw the hidden tests or the reference.** The EGM sessions ran in a sandbox that hid the experiments folder and the whole work folder except the run's own. The baseline transcripts never mention the reference or hidden-test clones, which were deleted after the baseline runs.
- **Grading was complete.** Every run ran all 16 hidden tests and the whole existing suite.

## Approver messages

| # | EGM 1 | EGM 2 |
| --- | --- | --- |
| 1 | start: `$egm:egm-draft` and the task ([arms/egm-start.md](arms/egm-start.md)) | the same |
| 2–6 | approve each drafted section (4) | "Yes, draft that section", then approve each section (5) |
| 7 | `$egm:egm-review`, interactive mode | the same, plus "proceed without additional context files" |
| — | **method correction**: discard the review, run it as the skill says, with reviewers spawned `fork_turns "none"`, stage by stage | the same correction |
| — | proceed at stages 5, 6, 8; resolve at 7 and 9; "auto accept" twice | the same ("leave it unchanged" where asked to revise at 5 and 6) |
| last | build, in a fresh session: "Implement the approved design in design_draft.md" ([arms/egm-build.md](arms/egm-build.md)) | the same |

## What changed from the design

- **The task.** LOWSTOCK was replaced by DISCOUNT after its baseline passed every test (README, amendment log).
- **The approver rule** gained one clause after run 1's first review: when the session audit shows that reviewers did not run as EGM specifies, the approver asks for the stage to be rerun as the skill says. This adds nothing about the requirements. It was used once in each run.
- **Codex flag.** EGM runs used `--enable multi_agent_v2`, which the design had not foreseen. The build sessions did not use it, matching the baselines.

## Reproducing

```
scripts/make_egm_home.sh ~/code/benchmark/skills-impact-work         # EGM at d651fe8, in a throwaway Codex home
trialrig run trial-none-discount.toml --out <dir> --agent codex       # baseline
EGM_ARGS="--enable multi_agent_v2" scripts/egm_drive.sh start egmN DISCOUNT arms/egm-start.md
EGM_ARGS="--enable multi_agent_v2" scripts/egm_drive.sh say egmN <message file>     # once per gate, following the rule
scripts/egm_drive.sh new egmN arms/egm-build.md                       # the build
scripts/egm_drive.sh grade egmN
python3 -I scripts/audit_sessions.py results/egmN/sessions

# follow-up: medium-effort build of an approved design, and its rival
scripts/egm_drive.sh seed egmNm DISCOUNT results/egmN/design/design_draft.md
EGM_ARGS='-c model_reasoning_effort="medium"' scripts/egm_drive.sh new egmNm arms/egm-build.md
scripts/egm_drive.sh grade egmNm
trialrig run trial-medium-discount.toml --out <dir> --agent codex
scripts/diag_line_name.sh <agent.diff> <out dir>                    # the diagnostic

# follow-up 2: Claude approver (a fresh Claude subagent per run, given arms/approver-brief.md; replies relayed verbatim)
EGM_ARGS='--enable multi_agent_v2 -c model_reasoning_effort="medium"' scripts/egm_drive.sh start eaN DISCOUNT arms/egm-start.md
EGM_HOME_SRC=home-plain EGM_ARGS='-c model_reasoning_effort="medium"' scripts/egm_drive.sh start paN DISCOUNT arms/plan-start.md
scripts/egm_drive.sh say <run> <run>/msgs/NN.md                      # each approver reply; arms/egm-review-start.md after the EGM draft is approved
EGM_ARGS='-c model_reasoning_effort="medium"' scripts/egm_drive.sh new <run> arms/egm-build.md
scripts/egm_drive.sh grade <run>
scripts/export_run.sh <run> <approver transcript>                     # also runs audit_sessions.py and audit_approver.py
uv run --with matplotlib python3 -I scripts/charts.py <out dir> [font dir]   # the website chart
```
