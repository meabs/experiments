# Elephant-Goldfish Model on a feature task: pilot (Codex)

**Pilot design, written 2026-10-23 before any EGM run; changes are in the amendment log. Results are in [REPORT.md](REPORT.md).** A pilot, not an experiment: it checks that the method can be run and graded, and measures its cost, before a full trial is designed. Its results are not evidence for or against EGM.

## What is being tried

[EGM](https://egm.dev) (the Elephant-Goldfish Model, google/elephant-goldfish-model, Apache 2.0) is a plugin for writing a design spec with AI agents before any code is written:

- **The Elephant**, the main agent with full context, drafts a design document section by section.
- **The Goldfish**, reviewer subagents started with no conversation history, read only the draft and the code, and report what it assumes without saying. The review has five stages: zoom out, comprehension, critique (three reviewers), a second zoom out, and implementation readiness (three reviewers).
- **A person approves** each drafted section and each review stage, and the approved spec is handed to a coding agent.

The site's claim is that "thousands of Google engineers use this open-source plugin to draft specs". It publishes no measure of whether the code built from the spec is more correct.

## Why a feature, not the usual tasks

The last five experiments used 20 small fixes. EGM is meant for features, where a spec has decisions to make. So this pilot uses one new feature task.

**First attempt, LOWSTOCK** ([prompt](tasks/LOWSTOCK/prompt.md)): an admin report of products at or below a stock threshold, with a fixed API.

- 9 hidden API tests ([hidden/LOWSTOCK](hidden/LOWSTOCK/)), validated against a reference implementation ([reference/LOWSTOCK.patch](reference/LOWSTOCK.patch)): all pass with it, 8 of 9 fail on the original code, and the whole existing suite still passes.
- During validation, a test of a product with two inventory entries was dropped: adding a second entry fails in the original code (a null pointer in `PersistableInventoryMapper`), an unrelated bug.
- **Dropped before any EGM run:** both baseline runs passed all 9 tests in under a minute. The prompt fixed every decision, leaving nothing for a spec to add.

**The task used, DISCOUNT** ([prompt](tasks/DISCOUNT/prompt.md)): merchant-managed discount codes that replace shopizer's single hard-coded promo rule. It states the need and fixes only the interface the tests use (the admin API's paths and JSON fields, and the existing cart promo endpoint). It touches persistence, an admin API, validation, cart totals, the category hierarchy and the existing promo pipeline.

- 16 hidden API tests ([hidden/DISCOUNT](hidden/DISCOUNT/)) on percentage and amount discounts, rounding, categories and their subcategories, minimum subtotal, dates, replacing and keeping codes, dropping codes when they stop applying, validation, uniqueness, stores and admin-only access.
- Validated against a reference implementation ([reference/DISCOUNT.patch](reference/DISCOUNT.patch), 7 files, about 440 added lines across 4 modules): all 16 pass with it and the whole existing suite still passes; 15 of 16 fail on the original code (admin-only access is already enforced).

## Arms in the pilot

| Arm | Runs | What the agent gets |
| --- | --- | --- |
| none | 2 | The task only, through the rig, as in the last five experiments |
| EGM | 2 | `egm-draft` on the task, then `egm-review` (all five stages), then a fresh session that implements the approved spec |

Codex `gpt-5.6-luna` at low effort, clean home, shopizer at `6a4a0a6`, the same grading as before (hidden tests plus the whole existing suite, and the relevance check on the agent's own tests). EGM is installed from the plugin's repository at commit `d651fe8` into the EGM arm's home only.

## I acted as the human approver, to make this scalable

EGM expects a person at every gate. A full trial of 60 or more EGM runs cannot have a person in each, so this pilot tests whether a fixed approval rule, which a script or a model could later follow, is enough. **Claude (the assistant running these experiments) acted as the approver**, following this rule, and every message it sent is saved with the run:

- **Requirements come only from the task text.** When the agent asks something the task answers, the approver quotes the task. When the task does not answer it, the approver says to decide, record the decision in the document, and move on. The approver knows the hidden tests, so it adds no requirement of its own.
- **A drafted section is approved** unless it contradicts the task text. If it does, the approver quotes the sentence it contradicts.
- **Review:** the interactive preset, with all five stages. At stages 5, 6 and 8 the approver proceeds. At stages 7 and 9 it chooses "Resolve findings with agent", and approves the proposed fixes unless one contradicts the task text.
- **Build:** a fresh Codex session in the same clone is asked to implement the approved design, given only the spec's path, as EGM describes handing the spec to a coding agent.
- **Method (added after run 1's first review; see the amendment log):** when the session audit shows that reviewers did not run as EGM specifies (for example, spawned with the whole conversation instead of a fresh context), the approver asks for the stage to be rerun as the skill says. This adds nothing about the requirements.

This is the main limit of the pilot: EGM without a human's judgement. A real engineer would also bring knowledge the task text does not contain.

## What the pilot measures

- Whether EGM runs end to end under Codex `exec` with resumed sessions, and whether the Goldfish really run as separate subagents (checked from the transcripts, not from the agent's own report).
- Tokens, cost, time and number of approver turns per EGM run, to price a full trial.
- Hidden tests passed, per run, for both arms. With 2 or 3 runs per arm, this is a sanity check, not a comparison.

## Follow-up 2: a Claude approver using judgement (design written 2026-10-23, before any run)

In the pilot the approver followed a rule, because Claude, who ran the pilot, knew the hidden tests. Follow-up 2 asks whether an approver who uses judgement gets more out of EGM. The approver is a **fresh Claude agent per run that has never seen the hidden tests or the reference**.

**The approver** (Claude Opus 5.5, a subagent started with no conversation history):

- gets only the brief ([arms/approver-brief.md](arms/approver-brief.md)), which holds the task text and the path of the run's clone, then each of the coding agent's messages, verbatim;
- may read the clone, to check what the design says about the code. It is told not to read anything else and not to edit files. Its tool calls are audited afterwards for any path outside the clone;
- answers each gate as the engineer who asked for the feature: approve, push back, ask for changes, choose among options. Its replies are sent to the coding agent verbatim, and saved;
- has 25 messages per run at most.

Claude, running the experiment, only relays messages, apart from fixed operator messages: the start ([arms/egm-start.md](arms/egm-start.md) or [arms/plan-start.md](arms/plan-start.md)), and in EGM runs the review start once the approver approves the draft ([arms/egm-review-start.md](arms/egm-review-start.md)). The review start includes, up front, the pilot's method correction (spawn every reviewer with `fork_turns "none"`, one stage at a time). The plan arm's Codex home is a fresh one without the plugin (`home-plain`). Claude still applies the pilot's method clause (asking for a review stage to be rerun if the session audit shows reviewers spawned with the whole conversation), but adds nothing about the requirements.

**Arms** (Codex `gpt-5.6-luna`, **medium effort in every session**; DISCOUNT; same grading):

| Arm | Runs | What happens |
| --- | --- | --- |
| EGM + approver | 3 | `egm-draft`, then `egm-review` (interactive, all five stages), with the approver at every gate; then a fresh session builds from the approved design ([arms/egm-build.md](arms/egm-build.md)) |
| plan + approver | 3 | Codex without EGM writes a design to `design_draft.md` ([arms/plan-start.md](arms/plan-start.md)); the approver reviews it, as often as it wants; then the same fresh build session |
| plain (existing) | 2 | Task only, medium effort: the follow-up's baseline (4/16 twice; 13/16 twice on the diagnostic) |

The plan arm controls for the approver: if EGM + approver does no better than plan + approver, any gain is the approver's, not EGM's.

**Measures, fixed now:** hidden tests passed (the score), and the line-name diagnostic ([scripts/diag_line_name.sh](scripts/diag_line_name.sh)) as a secondary measure; cost of the Codex sessions; number of approver messages; whether the approved design names the totals line `discount`. With 3 runs per arm this is still a pilot: differences of a test or two mean nothing.

## Amendment log

- 2026-10-23: pilot written at the user's request: "Do the pilot run but actually do a feature, you act as the human approver, be clear in write up we did this to scale the experiment".
- 2026-10-23, after the LOWSTOCK baseline and before any EGM run: LOWSTOCK replaced by DISCOUNT, at the user's request ("make feature harder really hard").
- 2026-10-23, during EGM run 1, before any result: the method clause added to the approver rule, after the session audit showed reviewers spawned with `fork_turns: "all"`. EGM runs use `--enable multi_agent_v2`, without which Codex 0.157 has no subagent tool.
- 2026-10-23, after both EGM runs: the listing test accepts a paginated object as well as an array (the task does not fix the shape). No result changed.
- 2026-10-23, after the pilot: a follow-up, at the user's request ("Go for it", to fix the build step and test the fix). The two approved designs were each built again in a fresh clone by a Codex session at medium effort, and plain Codex at medium effort ran the task alone twice as the rival. After grading, a diagnostic that also accepts a totals line named `order.total.discount` was added. It is reported beside the score and does not replace it.
