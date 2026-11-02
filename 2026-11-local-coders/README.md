# Which local coding model is good enough to drive a coding agent? (local coders)

**Status:** design, written before any measured run. Changes after this point go in the [amendment log](#amendment-log).

## Question

Earlier local runs left a gap. `qwen3:8b` couldn't drive Codex at all; `qwen3.8:27b` could, at about 22 minutes a run;
`qwen3-coder:30b` was downloaded and never tested. Public coding benchmarks don't say whether a model can drive a real
agent harness on someone's own repository.

With the same Codex harness, sandbox and tasks from two earlier experiments:

1. **Which open-weight models can drive Codex at all** (read files, edit, run tests, finish)?
2. **How often does each one get the task right,** judged by hidden tests?
3. **What does a pass cost** in time and energy on this machine?
4. **Does any of them reach a "good enough" bar,** set before the runs (below)?

The result is a short leaderboard on our own tasks, not a general benchmark.

## Models

All run through Ollama on this machine (AMD Ryzen AI Max, ROCm, 32 GB GPU carve-out), 4-bit quantised (flint: its default `40b-a2b` int4 tag), context 65,536,
through Codex 0.157's local profile (`~/code/benchmark/local-setup`), medium reasoning effort, web search off.

| Model | Maker | Type | Download | Status |
| --- | --- | --- | --- | --- |
| `qwen3-coder:30b` | Alibaba Qwen | mixture of experts, coding | 18 GB | installed, never tested in Codex |
| `qwen3.8:27b` | Alibaba Qwen | dense, general | 17 GB | installed; okf-local's model (reference) |
| `devstral-small-2:24b` | Mistral | dense, built for coding agents | 15 GB | to download |
| `gpt-oss:20b` | OpenAI | mixture of experts, reasoning and tools | 14 GB | to download |
| `flint:40b` | Recursive | mixture of experts (about 2B active), built for coding agents; released late October 2026 | 23 GB | to download |

Each model gets its own entry in Codex's model catalog, cloned from the existing local entry with only the name and
context changed. Exact versions (Ollama digests) are recorded before the pilot.

**Hosted reference, not rerun:** `gpt-5.6-luna`'s published results on the same tasks (okf-local's test G source and
broken-tools' F0 runs), labelled as a reference from another Codex version, not part of any test.

## Tasks

Eight tasks from two experiments, chosen because hidden tests already grade them:

- **Set S, storefront (JavaScript, 4 tasks):** okf-local's four cross-repository changes in its `okf` arm, where the
  backend's guide is in the repository. This checks whether a model can use facts it's given.
- **Set J, accounts API (Java/Spring, 4 tickets):** broken-tools' C1, C2, L1X and S2X with no fault (F0) and the plain
  AGENTS.md (arm A). Feature work with authorisation rules, built and tested with Maven.

Same prompts, sandboxes, graders and hidden tests as the original experiments.

## Size

5 models × 8 tasks × 3 runs = **120 runs**. Time limit: 30 minutes a run (a timeout is a fail). Runs go model by
model (loading a model takes minutes), tasks in shuffled order within each model (seed 1).

## Measures

- **Pass (primary):** the run finished within the time limit and the task's hidden test passes.
- **Drove the harness:** the run changed at least one file and ended with a final message (no crash, no stall, no
  refusal to act).
- **False success claim:** the final message says the change works or the tests pass, and the hidden test fails.
  Coded by `openai/gpt-6-luna` via OpenRouter from the final message and the grade; I check every positive label.
- **Time:** wall time per run, median and per pass.
- **Energy:** APU package power (the only sensor) logged during each run; watt-hours per run and per pass.
- **Tokens:** from Codex's event stream.

**"Good enough", fixed before the runs:** at least 10 of 12 passes on *each* set, and a median run of 10 minutes or
less. A model either clears it or doesn't; the leaderboard shows how far each is from it.

## Hypotheses and analysis

- **H1.** `qwen3-coder:30b` passes a different share of runs than `qwen3.8:27b` (two-sided).
- **H2–H4.** `devstral-small-2`, `gpt-oss:20b` and `flint:40b` each pass a different share than `qwen3.8:27b`
  (two-sided).
- **Analysis:**
  - Unit: the run.
  - Permutation tests shuffle model labels within task (10,000, seed 1); Holm over H1–H4.
  - Wilson 95% intervals for pass rates.
  - Everything else is descriptive.
  - "No measurable difference" where a test isn't significant.

## Pilot (before the main run)

- **Runs:** one run per model per task (40 runs, not part of the main run).
- **Checks:**
  - Each model can drive Codex. A model that makes no edit in all 8 pilot runs is dropped and reported, as `qwen3:8b` was.
  - Each model's context fits in GPU memory.
  - Graders pass on every reference solution.
- **Ceiling:** if every model passes every pilot run of set S, set S is still reported but isn't used to rank the models.

## What it does not show

- **One harness.** Codex with a catalog entry adapted for Ollama (no custom tools, as in okf-local). A harness built
  for a given model might do better.
- **8 tasks, 2 repositories, 3 runs each.** The leaderboard holds for these tasks; differences of a run or two are noise.
- **4-bit quantisation, one machine.** Larger quantisations or other hardware change speed and possibly quality.
- **Models change fast.** The leaderboard is for these versions on this date.

## Amendment log

(none yet)
