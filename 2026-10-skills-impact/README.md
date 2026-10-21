# Do popular agent skills make a difference?

Written 2026-10-21, before any measured run. Changes made after this point go in the amendment log at the bottom, with the date and the reason.

## Question

Widely shared skill packs claim that they make coding agents more correct (test-first development, systematic debugging, checking before claiming done) or cheaper (terse output). Do they, on real tasks in a large repository, for two agents other than the one they were mainly written for?

## Agents

| Agent | CLI | Model | Why |
| --- | --- | --- | --- |
| Codex | `codex exec --json` (0.157.0) | `gpt-5.6-luna`, reasoning effort high | Same as Experiments 2 to 5, so results compare |
| Cursor | `cursor-agent -p` (2026.10.01) | `grok-4.7-low` | Cheapest Grok in Cursor: 4.7 and 4.6 bill the same per token, `-fast` variants bill 2x, and low effort spends the fewest reasoning tokens |

CLI versions are pinned for the whole experiment, with auto-update off. The rig records each run's version, and a run with a different version is invalid.

The two agents are never compared with each other. Their token totals mean different things.

## Repository

[shopizer](https://github.com/shopizer-ecommerce/shopizer), pinned at commit `6a4a0a6`. It is a Java 11+ Maven multi-module e-commerce platform with about 1,200 Java files. Builds use JDK 21 (`/opt/homebrew/opt/openjdk@21`) and run offline against a pre-warmed `~/.m2`. Experiments 2 and 3 used the same checkout.

## Arms

Each arm installs skills into the repository's `.agents/skills/`, which both CLIs read (checked 2026-10-21 with a probe skill). Each skill pack is pinned to a commit hash, recorded in `arms/<arm>/SOURCE`. When the vendor's install guide for Codex or Cursor also says to add an `AGENTS.md` line, that line is added as well, because it is part of the product as shipped.

| Arm | Contents | What it tests |
| --- | --- | --- |
| `none` | Nothing | Control |
| `placebo` | One skill of about the same length as the largest pack's entry skill, with generic advice ("read the code before changing it, keep changes small") and a broad description | Whether any extra skill text has an effect |
| `superpowers` | [obra/superpowers](https://github.com/obra/superpowers) as its Codex and Cursor install guides describe it, including `using-superpowers`, `test-driven-development`, `systematic-debugging` and `verification-before-completion` | The best-known workflow pack |
| `pocock` | [mattpocock/skills](https://github.com/mattpocock/skills), the 27 skills its plugin manifest installs (11 of them model-invocable, including `tdd`, `diagnosing-bugs`, `codebase-design` and `code-review`) | A second widely used pack, with a smaller and more targeted set |
| `pstack` (Cursor only) | [cursor/plugins `pstack`](https://github.com/cursor/plugins/tree/main/pstack) 0.15.29 (commit `190d287`, 2026-10-20), installed as a Cursor plugin in the clean home | Cursor's widely promoted "rigorous engineering" pack |

**pstack needs three adjustments, all recorded as part of the treatment:**

1. Its entry skill `poteto-mode` sets `disable-model-invocation: true`, so it never starts on its own. The vendor's usage is to begin the prompt with `/poteto-mode`, so this arm's prompt is the task prompt with that prefix. The gate checks that headless `cursor-agent -p` honours the prefix. If it does not, the prompt instead says "Use the poteto-mode skill", and the change is logged.
2. By default it hands code to `grok-4.7-xhigh-fast` subagents and judgment to `claude-opus-5-5-xhigh` subagents. That would change the model under test and multiply the cost. The arm writes `~/.cursor/rules/pstack-models.mdc` (the file `/setup-pstack` writes) with every role set to `inherit-parent`, so all subagents run on `grok-4.7-low`. Panel sizes stay as shipped.
3. It ships for Cursor and Claude Code only, so there is no Codex cell.

The gate also checks that Cursor's `stream-json` usage includes subagent tokens. If it does not, pstack's cost is undercounted and is reported as a lower bound.

Two packs were left out: Anthropic's `anthropics/skills`, because it holds document and design skills with nothing for a Java backend, and the Vercel React rules, because shopizer has no frontend.

### Isolation (the main threat)

On this machine, a probe on 2026-10-21 found that **both agents already see every skill in the home folder** (`~/.agents/skills`, `~/.claude/skills`, `~/.cursor/skills`, `~/.codex/skills`), including `tdd`, `caveman`, `diagnose` and `using-superpowers`. Cursor also loads Claude plugin skills. Without isolation, the control arm would carry the treatment. Each run therefore gets:

1. A clean `HOME` (and `CODEX_HOME`) holding only the agent's login, set through the rig agent's `env`.
2. A fallback if a CLI does not log in under a clean home: the rig's `isolate` setting, which uses macOS `sandbox-exec` to deny reads of those four folders and `~/.claude/plugins`.

The built-in skills that ship inside each CLI (Codex: `skill-creator`, `openai-docs` and others; Cursor: `create-skill`, `review-bugbot` and others) stay in every arm and are reported as a constant background.

**Gate before any measured run:** in each arm and for each agent, ask "list every skill available to you". `none` must list only the built-in skills, and each treatment arm must list the built-in skills plus exactly its own. If an arm fails, the experiment does not start.

## Tasks

The prompts never mention skills, documentation or tools. The hidden tests live outside the clone (and are denied to the agent through `isolate`), and are copied in only by the `verify` command after the agent finishes.

| ID | Kind | Task | Verified by | Skills it targets |
| --- | --- | --- | --- | --- |
| `BUG` | Bug fix | A planted regression in `sm-core` business logic (for example, pagination or price calculation), reported as a user symptom ("customers on page 2 see the last item of page 1 again"). The plant is a one-line change that the module's existing tests do not catch | A hidden JUnit test for the symptom, plus the module's own tests, plus a compile of the whole reactor | `systematic-debugging`, `diagnose`, `tdd` |
| `FEAT` | Small feature | A new rule in an existing service, with two edge cases written into the prompt (for example, a coupon-code validation rule) | A hidden JUnit test of the rule and its edge cases, plus the module's tests and a reactor compile. Whether the agent added tests of its own is recorded separately | `test-driven-development`, `tdd`, `verification-before-completion` |
| `CROSS` | Multi-file change | Add a field end to end: entity, service, API model, mapper, and one REST response, with one existing caller that must keep working | A hidden API-level test, plus the tests of every touched module and a reactor compile | Planning and verification skills; pstack's "go deep first" |

The experiment is about making effective changes, so every task is a change task. Caveman, a token-saving skill, is tested in its own experiment: [2026-10-caveman](../2026-10-caveman/).

**Effective change, measured from the final repository and never from what the agent says:**

- **Correct**: the hidden test passes.
- **No regressions**: the existing tests of every module the agent touched still pass.
- **Builds**: the whole reactor compiles.
- **Focused**: the number of lines changed compared with the reference solution, and any files changed outside the modules the task needs (reported, not part of pass).
- **Tests that bite**: for `BUG`, the agent's own new tests are run against the unfixed code. A test that also passes there does not catch the bug. The TDD skills claim to produce tests that do.

**Calibration first.** Past experiments here hit the ceiling: agents passed whether or not they had help. Before the tasks are frozen, `none` runs each task 3 times per agent. A change task is kept only if the control passes between 1 and 2 of 3 times on at least one agent. Otherwise it is made harder or easier and calibrated again, and every attempt is logged. The calibration runs are not part of the results.

**Step 0 (feasibility), done 2026-10-21:** the whole reactor's tests run offline under JDK 21 (`sm-core` in 20 s, `sm-shop` REST integration tests in 27 s). The verifier is `scripts/verify.sh`: it saves the agent's diff, copies in the hidden test and runs `mvn -o clean test` on the whole reactor. It must clean, because a stale compiled test in `target/` gave a false failure while the tasks were built.

## Measures

Primary:

1. **Verified pass**: the `verify` exit code. Timeouts (20 minutes) and crashes count as failures.
2. **Total tokens per run**, relative to `none` for the same agent and task (the rig's relative-cost bootstrap).

Secondary:

- **Skill uptake** (manipulation check): runs whose tool calls read a `SKILL.md` (`uses = "skills/.+/SKILL\\.md"`). Cursor can inject a skill without a tool call, so the rig's `claim` line also asks which skills were used, reported as self-reported.
- Codex dollar cost ($0.20, $0.02 and $1.20 per million fresh-input, cached-input and output tokens) and Cursor dollar cost at the published Grok 4.7 rate ($2 per million input, $6 per million output)
- Wall time, turns and Maven runs
- **Test-first**: whether the first edit under `src/test` comes before the first edit under `src/main` (the TDD skills' central claim)
- Whether the agent added tests, and the size of its diff
- Overclaims: the agent says it passed but `verify` fails (the rig's `claim = true`)

## Hypotheses and decision rules

These are fixed now. Each treatment arm is compared with `none`, and `placebo` is used to read the result.

| # | Hypothesis | Supported if |
| --- | --- | --- |
| H1 | `superpowers` raises the pass rate on `BUG` and `FEAT` | Pooled across both agents and both tasks, the pass rate is higher than `none` with a one-sided Fisher p < 0.05 |
| H2 | `pocock` raises the pass rate on `BUG` and `FEAT` | Same test as H1 |
| H4 | The TDD packs (`superpowers`, `pocock`, `pstack`) produce tests that bite | On `BUG`, a larger share of their runs add a test that fails on the unfixed code than in `none` (Fisher p < 0.05) |
| H7 | `pstack` raises the pass rate on Cursor | Pooled over `BUG`, `FEAT` and `CROSS` (18 runs), the pass rate is higher than Cursor `none`, with a one-sided Fisher p < 0.05. Its token cost is reported alongside |
| H5 | The packs make agents work test-first | `superpowers` or `pocock` is test-first in a larger share of change runs than `none` (Fisher p < 0.05) |
| H6 | The packs reduce overclaiming | Fewer overclaims than `none`. Reported as descriptive only, since overclaims are expected to be rare |

Reading the results: if `placebo` moves as much as a pack does, the effect is "more instructions in context", not the pack itself. If a pack's skill uptake is under 50%, a null result means the skill was rarely triggered, not that it does not work. In that case a follow-up arm names the skill in the prompt, matched by the same wording in the control.

Predictions, written down now so they can be checked: ceiling effects keep H1 and H2 small at best, and the packs cost more tokens than `none`.

## Size, order and stopping

- **Stage 1**: 6 runs per cell. 3 tasks × 4 arms × 2 agents × 6 = 144 runs, plus `pstack` on Cursor (3 × 6 = 18), giving **162 runs**. Runs are interleaved: each repetition runs every task, arm and agent before the next repetition starts, so no arm runs as a block. Codex runs first, then Cursor, to avoid six Maven builds at once. `parallel = 3` (Maven needs memory).
- **Stage 2**: `trialrig plan --results results/stage1 --max-reps 12`. Cells still marked open get more runs, up to 12 per arm, if the spend allows. Extra runs taken after looking at the data are reported as sequential, and their p-values are marked as such.
- **Power, stated plainly**: at 6 runs a cell, only very large differences show up within a cell (about 1 of 6 against 5 of 6). Pooled across 2 agents and 3 change tasks (36 runs an arm), a difference of about 35 percentage points is detectable. Token differences under about 20% are not reliable at this size and are reported as "no evidence", not as "no effect".

## Estimated cost and time

These figures come from the token counts Experiment 3 recorded on shopizer, priced at the rates above with no cache discount for Cursor:

- Codex change runs: 0.3 to 1.2 million tokens, about 90% of them cached, so $0.03 to $0.10 a run.
- Cursor change runs: 30k to 80k tokens, so $0.06 to $0.16 a run.
- `pstack` runs: assumed to cost 3 to 10 times a Cursor change run, because of its subagents.

Stage 1 comes to about **$10 to $50** (`pstack` is the most uncertain part) and **about 7 hours** of wall time at `parallel = 3`. The Mac is kept awake with a detached `caffeinate -dimsu`.

## Grading integrity

- The hidden tests and keys are written and checked against a reference solution before any arm runs, and they are never placed in the clone during a run.
- `rescore` is allowed only to fix a key defect that is shown with evidence. Both scores are reported.
- Under the doc-gap rule from earlier experiments, a failure caused by a skill's bad advice (for example, a wrong Maven command) is a finding about the skill. It is reported, but it is not fixed and re-run, because the treatment is the pack as published.

## Known limits

- One repository, one language, two agents, and models chosen for cost, not capability. The packs are written mainly for Claude Code.
- The tasks are written by Claude, which also wrote the hidden tests. A reviewer should read them before the run.
- Each agent's built-in skills are a constant background in every arm.
- This repository is public, and raw agent logs are committed. Before pushing, logs are checked for absolute home paths and tokens.

## Layout

```
2026-10-skills-impact/
  README.md          this design
  trial.toml         AgentTrialRig trial (added when tasks are frozen)
  arms/<arm>/        overlay copied into each clone, plus SOURCE (pack commit hash)
  tasks/             prompts, plants, reference solutions
  hidden/            hidden tests (never copied into a clone before verify)
  results/           raw runs, report.md, RESULTS.md
```

## Amendment log

- 2026-10-21: design written.
- 2026-10-21 (before any run): cost estimate corrected from $60–170 to the measured token counts of Experiment 3. `QA` cut to `none` and `caveman`. `CROSS` change task and "effective change" measures added. `pstack` arm added (Cursor only, invoked through `/poteto-mode`, every model role set to `inherit-parent`). H4 changed from "pack overhead on QA" to "tests that bite"; H7 added.
- 2026-10-21 (before any run), tasks and arms built:
  - `BUG` plants a copy-paste slip in `ProductPriceUtils.finalPrice` (a special with both dates checks the start date twice, so it never applies). The existing suite passes with the plant. Hidden test: 4 cases of the date window.
  - `FEAT`: the cart limit of 99, over `POST /cart`, `PUT /cart/{code}` and `POST /cart/{code}/multi`. Hidden test: 4 API tests.
  - `CROSS`: manufacturer `website`, over the entity, the API model, two populators, a mapper, the product populator and API validation. Create and update swallow exceptions into 503, so a 400 needs a deliberate design. Hidden test: 5 API tests against the JSON.
  - Each hidden test fails on the starting code and passes on `tasks/<id>/reference.patch`. The full suite passes with each reference applied.
  - `setup.sh` replaces git history with one commit, so the plant cannot be found by diffing.
  - Arms come from pinned commits through `scripts/build_arms.sh`. `superpowers` is all 15 skills, and the text its `sessionStart` hook injects goes in `AGENTS.md`, because plugin folders are blocked by isolation. `pocock` is the 27 skills in its plugin manifest; Matt Pocock's `diagnose` is now `diagnosing-bugs`, and `zoom-out` is no longer published. `pstack` is its skills and agents as project files, plus the model rule.
  - Isolation: Codex runs with a clean `HOME` and `CODEX_HOME`, which also hides `~/.codex/AGENTS.md` and Codex memories. Cursor cannot log in under a clean home, so it runs with the real home and the rig's `isolate` blocks the skill, plugin and agent folders. Both are blocked from this repository, where the hidden tests live.
  - AgentTrialRig changes: an arm-level `prompt_prefix` (for `/poteto-mode`), and an `isolate` fix (see `results/gate.md`).
- 2026-10-21 (before any run), calibration (`results/calibration.md`): BUG and FEAT were at the ceiling. BUG is now v3, two independent slips behind one symptom; the hidden test is API-level, 5 cases. FEAT v2 reads the limit from merchant configuration and is still at the ceiling. The user chose to keep it for cost and process measures, so the pass-rate hypotheses (H1, H2, H7) pool over BUG and CROSS only, and FEAT pass rates are reported as descriptive. CROSS is unchanged. Pass is now defined as: the reactor ran, every hidden test passed, and no other test failed, including tests the agent added. The verifier runs every module and writes `verify-summary.json`.
- 2026-10-21 (before any run): `caveman` moved to its own experiment ([2026-10-caveman](../2026-10-caveman/)) at the user's request. `QA` and H3 removed from this one. 162 runs.
