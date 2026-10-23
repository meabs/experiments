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
- **EGM's review did not run as specified until corrected.** In both runs, Codex at low effort first spawned its reviewers with `fork_turns: "all"`, which copies the whole conversation into each one, so they were not Goldfish. It also merged review stages. After one correction from the approver (below), every later reviewer was spawned with fresh context (`fork_turns: "none"`), and each stage stopped at its own checkpoint. Run 2 still ran one combined critic at stage 7 instead of EGM's three.

## What a full trial would cost

- **EGM run:** about $0.22 to $0.29 and 7 to 9 minutes at low effort, plus about 17 approver messages. That is within the earlier estimate of $0.25 to $1.00. About $0.06 of run 1 went on the discarded first review.
- **60 EGM runs:** about $15 to $20; with baseline, plan-first and medium-effort arms, about $25 to $35 in all.
- **The approver:**
  - the approval rule is mechanical: approve, proceed, resolve, then auto accept;
  - the one judgement it needed, catching full-context reviewers, came from the session audit, which a script can do.

  So a scripted approver is feasible.
- **The tasks are the expensive part.** DISCOUNT took several hours to build: the prompt, 16 hidden tests and a reference implementation, each checked against the original code and the whole suite. A trial would need 10 or more such features.

## What the pilot changes for a full design

1. **Fix the build step before measuring anything else.** With a low-effort build, EGM's output is limited by how much code the build writes, not by the spec. A full trial should try the build at medium effort, or in the Elephant's own session, or with a check that every planned file was changed. Otherwise it measures the build agent, not EGM.
2. **Turn on Codex's subagents explicitly** (`--enable multi_agent_v2`). Without it, Codex 0.157 offers no spawn tool and EGM cannot run its review.
3. **Audit every review automatically** from the session files: each subagent's `fork_turns`, its parent, and its tokens. Subagent tokens are not in the main event stream; they are only in the session files.
4. **Count each arm's fair rival.** To isolate EGM's effect, the arms should include the task alone at the same effort as the build, a plan-first arm without reviewers, and medium effort, which has been the only clear gain in earlier experiments.

## Problems found along the way

- **Shared Maven repository.** Twice, the shared `~/.m2` received modified shopizer jars:
  - once from my own `mvn install` while building the reference implementation;
  - once from EGM run 2's build agent, whose design told it to run `./mvnw -DskipTests install`.

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
```
