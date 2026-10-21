# Does caveman cut tokens without losing correctness?

Written 2026-10-21, before any measured run. Later changes go in the amendment log at the bottom.

## Question

[caveman](https://github.com/mattpocock/skills) (from mattpocock/skills) tells the agent to answer in compressed, telegraphic text, and claims to cut tokens by about 75% while keeping technical accuracy. Does it cut the tokens an agent actually uses on real work, and does correctness hold?

The claim is about the agent's replies, and replies are only part of a run. Most of a run's tokens are input: files read, tool output, and the context sent again on every turn. Caveman can only shrink output, and its own text adds a little input. So the experiment separates output tokens from total tokens.

## Shared setup

The following are the same as in [2026-10-skills-impact](../2026-10-skills-impact/), and are not repeated here:

- Agents: Codex `gpt-5.6-luna` (high) and Cursor `grok-4.7-low`, with the CLI versions pinned.
- Repository: shopizer at `6a4a0a6`.
- Isolation: a clean home, with `isolate` as the fallback, and the "list your skills" gate.
- Tasks `BUG` and `FEAT`, with their hidden tests and verifiers.

The runs are separate from skills-impact, with their own `none` control, in their own randomised order.

## Arms

| Arm | Contents |
| --- | --- |
| `none` | Nothing |
| `caveman` | `caveman` in `.agents/skills/`, pinned to a commit recorded in `arms/caveman/SOURCE`. It is installed only, not invoked, the same way the skills-impact packs are |

Uptake check: a run counts as having used the skill if it reads `caveman/SKILL.md`, or if its replies are visibly compressed (judged blind against a rubric written before the run). If uptake is under 50%, a follow-up arm names the skill in the prompt, with matching wording in a control.

## Tasks

| ID | Kind | Why it is here |
| --- | --- | --- |
| `QA` | The eight multi-step impact questions from Experiment 3 (`SU`), scored by F1 against bytecode-derived truth. Pass is a mean F1 of at least 0.95 | Its home ground: an answer made of text |
| `BUG`, `FEAT` | The change tasks from skills-impact | Whether the saving carries over to coding work, and whether compressed reasoning breaks changes |

## Measures

- Primary: total tokens relative to `none`, and pass rate (answer key for `QA`, `verify` for change tasks).
- Output tokens relative to `none`: the part caveman can actually affect.
- Codex dollar cost, Cursor dollar cost at Grok 4.7 rates, wall time and turns.
- The length in words of the final answer.

## Hypotheses

| # | Hypothesis | Supported if |
| --- | --- | --- |
| C1 | Caveman cuts output tokens | The relative-output interval lies entirely below 1.00 on at least one agent |
| C2 | Caveman cuts total tokens by at least 20% | The relative-cost interval lies entirely below 0.80 on at least one agent |
| C3 | Correctness holds | Pooled per agent, the pass rate is not lower than `none` by more than one run in six |

Prediction, written now: C1 holds, C2 fails (input dominates), C3 holds on `QA`, and C3 is unclear on change tasks.

## Size, cost and time

3 tasks × 2 arms × 2 agents × 6 runs = **72 runs**. Estimated cost, from Experiment 3's token counts:

- Codex: about $2.
- Cursor change runs: $1.50 to $4.
- Cursor `QA` runs: $6 to $12.

That is about **$10 to $18** in total, and about 3 hours at `parallel = 3`. Stage 2 adds runs only where `trialrig plan` marks a cell open, up to 12 a cell.

## Layout

`README.md` (this design), `trial.toml`, `arms/caveman/`, and `results/` (raw runs, `report.md`, `RESULTS.md`). The tasks and hidden tests are taken from `../2026-10-skills-impact/`.

## Amendment log

- 2026-10-21: design written, split out of skills-impact at the user's request.
