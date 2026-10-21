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
| `pocock` | [mattpocock/skills](https://github.com/mattpocock/skills), engineering skills relevant to backend code: `tdd`, `diagnose`, `zoom-out`, `codebase-design` | A second widely used pack, with a smaller and more targeted set |
| `caveman` | `caveman` alone (from mattpocock/skills) | The claim that it cuts tokens by about 75% while keeping accuracy |

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
| `QA` | Read-only | Eight multi-step impact questions from Experiment 3 (`SU`), scored by F1 against bytecode-derived truth. Pass is a mean F1 of at least 0.95 | Answer key (`expect` regexes per question) | `caveman` (token claim); pack overhead on non-coding work |

**Calibration first.** Past experiments here hit the ceiling: agents passed whether or not they had help. Before the tasks are frozen, `none` runs each task 3 times per agent. A change task is kept only if the control passes between 1 and 2 of 3 times on at least one agent. Otherwise it is made harder or easier and calibrated again, and every attempt is logged. The calibration runs are not part of the results.

**Step 0 (feasibility):** confirm that `sm-core` tests run offline under JDK 21 in under 5 minutes. Experiment 3 only compiled shopizer and never ran its tests. If they do not run, the verifier becomes the hidden test alone, run with `-pl sm-core -am -Dtest=...`.

## Measures

Primary:

1. **Verified pass**: the `verify` exit code for change tasks, and the answer key for `QA`. Timeouts (20 minutes) and crashes count as failures.
2. **Total tokens per run**, relative to `none` for the same agent and task (the rig's relative-cost bootstrap).

Secondary:

- **Skill uptake** (manipulation check): runs whose tool calls read a `SKILL.md` (`uses = "skills/.+/SKILL\\.md"`). Cursor can inject a skill without a tool call, so the rig's `claim` line also asks which skills were used, reported as self-reported.
- Output tokens on their own. Caveman can only cut output, and output is a small share of total.
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
| H3 | `caveman` cuts total tokens by at least 20% with no loss of correctness | The relative-cost interval lies entirely below 0.80 on at least one agent, and the pass rate is not lower by more than one run in six |
| H4 | The workflow packs cost more tokens on `QA` than `none` | The relative-cost interval lies entirely above 1.00 |
| H5 | The packs make agents work test-first | `superpowers` or `pocock` is test-first in a larger share of change runs than `none` (Fisher p < 0.05) |
| H6 | The packs reduce overclaiming | Fewer overclaims than `none`. Reported as descriptive only, since overclaims are expected to be rare |

Reading the results: if `placebo` moves as much as a pack does, the effect is "more instructions in context", not the pack itself. If a pack's skill uptake is under 50%, a null result means the skill was rarely triggered, not that it does not work. In that case a follow-up arm names the skill in the prompt, matched by the same wording in the control.

Predictions, written down now so they can be checked: H3 fails on total tokens (input dominates, and the caveman text adds input) but output tokens fall. Ceiling effects make H1 and H2 small at best.

## Size, order and stopping

- **Stage 1**: 6 runs per (task, arm, agent), giving 3 × 5 × 2 × 6 = **180 runs**. The order is randomised, with no arm run as a block. `parallel = 3` (Maven needs memory).
- **Stage 2**: `trialrig plan --results results/stage1 --max-reps 12`. Cells still marked open get more runs, up to 12 per arm, if the spend allows. Extra runs taken after looking at the data are reported as sequential, and their p-values are marked as such.
- **Power, stated plainly**: at 6 runs a cell, only very large differences show up within a cell (about 1 of 6 against 5 of 6). Pooled across 2 agents and 2 change tasks (24 runs an arm), a difference of about 35 percentage points is detectable. Token differences under about 20% are not reliable at this size and are reported as "no evidence", not as "no effect".

## Estimated cost and time

From Experiments 2 and 3 on shopizer: Codex uses roughly 0.3 to 1.2 million tokens per run (mostly cached), about $0.10 to $0.40 a run. Cursor at Grok 4.7 rates is roughly $0.50 to $1.50 a run, depending on cache billing. Stage 1 comes to about **$60 to $170** and **6 to 9 hours** of wall time at `parallel = 3`. The Mac is kept awake with a detached `caffeinate -dimsu`.

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
