# Does test-skill hold with a local open-weight model? (Codex, qwen3.8:27b)

**Final design, committed 2026-10-23 before any measured run.** Later changes go in the amendment log at the bottom.

## Why

This repeats [2026-10-test-skill](../2026-10-test-skill/) (experiment TSK) with one change: the model. TSK ran Codex with OpenAI's hosted `gpt-5.6-luna`. Here Codex runs an open-weight model on this machine. Everything else is copied: tasks, prompts, arms, hidden tests, grader, shopizer commit, reasoning-effort settings, repetitions and analysis.

Two reasons:

1. **Do TSK's findings depend on the model?** TSK found that a one-paragraph instruction got a real test in 56 of 60 runs, that the skill added nothing, that a Stop-hook gate worked as well as the instruction, and that only medium effort raised the pass rate significantly. A weaker, local model might respond to the same guidance differently.
2. **What does a local model cost in correctness, time and energy** on the same work?

The hosted results are not rerun. They come from TSK's `results/` at commit [`e3908706`](https://github.com/meabs/experiments/tree/e3908706a9278546408fdd462a0ae685ef98255b/2026-10-test-skill).

## Question

On TSK's 20 tasks and six arms, how does a local `qwen3.8:27b` compare with hosted `gpt-5.6-luna` in verified passes and relevant tests? Does it reproduce TSK's arm effects?

## Agent and repository

| | hosted (TSK, published) | local (this experiment) |
| --- | --- | --- |
| Model | `gpt-5.6-luna` (OpenAI) | **`qwen3.8:27b`**, 27.3B parameters, **Q4_K_M** quantization (GGUF), Ollama digest `aaee06c39dcf` |
| Server | OpenAI API | **Ollama 0.40.5**, ROCm 7.2, OpenAI-compatible Responses API (`/v1/responses`) |
| Hardware | (not applicable) | AMD Ryzen AI Max+ 395, Radeon 8060S iGPU (gfx1151) with 32 GB of 64 GB unified memory; the whole model is in GPU memory |
| Context length | 272,000 tokens | **65,536 tokens** (auto-compaction at 56,000) |
| Sampling | provider default | Ollama's model defaults, unchanged: temperature 1.0, top_k 20, top_p 0.95, presence penalty 0 |
| Reasoning effort | low (E: medium) | the same setting is passed (`model_reasoning_effort`); whether the server applies it is checked before the runs (below) |
| Codex CLI | 0.157 | 0.157.0 |
| Rig | trialrig reporting 0.6.1 | trialrig 0.7.0 (the runner differs only by macOS `isolate` and renamed claim labels) |
| Isolation | macOS `sandbox-exec` | bubblewrap ([`setup/codex-bwrap.sh`](setup/codex-bwrap.sh)), below |
| Parallel runs | 3 (main), 1 (E, F) | 1 for all (one GPU, one model slot) |
| OS, JDK | macOS, Homebrew openjdk 21 | Ubuntu 26.04.1, openjdk 21.0.12 |

- shopizer at `6a4a0a6` (Java, Maven, JDK 21), offline, as in TSK.
- **Tokens** are the units a model reads and writes, about four characters each. **Cached input** is input the server has already processed and reuses.
- **Reasoning effort** is a setting that tells the model how long to think before acting.

### Why the local Codex set-up differs (unavoidable)

Codex has no built-in entry for this model, and without one it falls back to generic tools. The local entry ([`setup/codex-catalog.json`](setup/codex-catalog.json)) is cloned from `gpt-5.6-luna`'s entry in Codex 0.157.0 ([`setup/make_catalog.py`](setup/make_catalog.py)), so the instructions, truncation and shell tool are luna's. Three changes were needed, because Ollama does not pass Codex's custom tools back correctly:

1. `use_responses_lite = false`. Ollama rejects the `additional_tools` input item (HTTP 400).
2. `tool_mode = null` instead of `code_mode_only`. The code-mode `exec` tool is a custom tool; its calls came back as plain function calls, Codex never answered them, and every call aborted.
3. `apply_patch_tool_type = null` instead of `freeform`, for the same reason. The agent edits files through the shell; `apply_patch` still works there as a command.

So the local agent has a slightly different tool set from the hosted one. This is part of what "the local model" means here, and it cannot be separated from the model.

### Isolation

The rig's `isolate` works only on macOS. Here Codex runs inside bubblewrap:

- `/` is read-only. `/home`, `/tmp` and `/run/user` are empty. Only the run's own clone is writable.
- The experiments folder (with the hidden tests), the real home configuration and every other run are invisible.
- Each run gets a fresh home and Codex configuration.
- The Maven repository is visible through an overlay with a throwaway upper layer: offline builds work, and anything the agent writes (for example `mvn install`) disappears with the run.
- The network is shared, because the model server is on `127.0.0.1`.

Proved by [`setup/isolation-test.sh`](setup/isolation-test.sh): 17 checks from inside the sandbox, plus the real agent told to print the hidden tests. Every attempt got "No such file or directory".

## Arms

Arms A to F are TSK's, copied unchanged from [`../2026-10-test-skill/arms`](../2026-10-test-skill/arms/) and its trial files at `e3908706`:

| Arm | Name | What the agent gets |
| --- | --- | --- |
| A | `none` | The task prompt only |
| B | `instruction` | The prompt starts with an instruction to write and run a focused API test of the change |
| C | `skill` | The same instruction, plus a pointer to the original `verify-api` skill |
| D | `skill-revised` | As C, with the revised skill |
| E | `medium` | The task prompt only, at medium reasoning effort |
| F | `gate` | The task prompt only, and a Stop hook that sends the agent back once if it has no relevant test |

An **arm** is one way of running the agent. TSK's README gives the exact texts.

**Arm G, local only, exploratory.** In the smoke test (below), the local agent made the correct fix early, then spent most of an hour building and rerunning its own Java harness in `/tmp` to check it, until the time limit. At the user's request ("anything we can add to stop it getting stuck creating the Java harness"), one extra arm tests a sentence aimed at that. A to F are unchanged, so the comparison with the hosted model stays clean. G is not compared with the hosted model.

| Arm | Name | What the agent gets |
| --- | --- | --- |
| G | `stop` | As A, with this before the task ([`arms/stop.md`](arms/stop.md)) |

> Once your change is made and compiles, stop and reply. Do not build your own harness, scripts or programs outside the project to check it.
>
> The task:

This wording was chosen after seeing one smoke-test run, so it is tuned to the behaviour seen there.

## Tasks

TSK's 20 tasks, plants and hidden tests, unchanged: [`../2026-10-test-skill/tasks`](../2026-10-test-skill/tasks/) and [`hidden`](../2026-10-test-skill/hidden/), at `e3908706`. The **hidden tests** are API-level JUnit tests the agent never sees; the grader adds them after the agent finishes.

## Size and cost

- **Local:** 20 tasks × 7 arms × 3 runs = **420 runs** (A to F 360, G 60).
- **Time limit per run, as TSK:** 30 minutes (F: 45 minutes). A run that times out is graded, but counts as a failure, as in TSK.
- **Estimated duration: about 5 to 8 days** of machine time, from the smoke tests. One run of A took the full 60 minutes allowed in the first smoke test. Grading adds 5 to 10 minutes per run.
- **No API bill.** Energy is about 85 W of APU package power while the agent runs (smoke test 1: 84 Wh in 60 minutes). At 0.25 £/kWh, about 2p a run, or roughly £10 for the trial.
- **Hosted calibration:** 20 runs of `gpt-5.6-luna` (arm A, 1 run per task), about $0.50 at TSK's prices. Approved by the user ("go ahead").

## Measures

For each run and both models:

- **Verified pass (primary):** the build ran, every hidden test ran and passed, and no existing test failed. As in TSK, the run must also have finished (status `ok`).
- **Relevant test:** TSK's primary measure ([`relevance.sh`](../2026-10-test-skill/scripts/relevance.sh)). The agent's own tests pass with its change, and at least one fails on the original code.
- **TSK's process measures:** wrote a test, ran tests, ran only `ActuatorTest`, read the skill, tried to start the app, and the gate's records.
- **Tokens:** input, cached input, output, reasoning. For a run that times out, the rig records none; they are taken from the run's Codex session file instead.
- **Wall time** per run: median and total.
- **Cost.**
  - Hosted: list prices with TSK's formula: (input − cached) × $0.20 + cached × $0.02 + output × $1.20, per million tokens.
  - Local: wall time; energy from APU package power ([`setup/powerlog.sh`](setup/powerlog.sh), once a second), at 0.25 £/kWh; and what the same tokens would cost at the hosted prices. The sensor measures the whole chip (CPU and GPU), so this is an upper bound on GPU energy.
- **False success claims:** failed runs whose final report says it passed (TSK's rule).
- **Failure modes,** from each failed run's events and Codex log, by fixed rules:
  - *timeout*: the time limit was reached;
  - *tool-call errors*: rejected or failed tool calls in Codex's log;
  - *malformed edits*: `apply_patch` failures, or edits that leave the code not compiling;
  - *gave up*: the final message says it could not finish;
  - *context overflow*: context-length errors, or compaction;
  - *looping*: the same command run 5 or more times;
  - *wrong fix*: none of the above; it finished, and failed the hidden tests.

  One run can have several. They are counted for both models, from the hosted runs' published events and logs too.

## Hypotheses and analysis (fixed before the runs)

The unit is the task. For each task and arm, a model's result is the number of runs, out of 3, that passed (or had a relevant test).

**Primary: local against hosted, verified passes, each arm A to F.**

| # | Hypothesis |
| --- | --- |
| L-A … L-F | In arm X, the local model's verified passes differ from the hosted model's |

- For each task: local passes (0 to 3) minus hosted passes (0 to 3).
- Two-sided exact sign-flip permutation test over the 20 tasks, and a bootstrap 95% interval over tasks (10,000 resamples, seed 1).
- Holm-adjusted together across the six arms at α = 0.05.
- A non-significant result is reported as "no measurable difference".

**Secondary,** reported but not tested as hypotheses (two-sided, unadjusted):

- Relevant tests, local against hosted, in each arm.
- **Does the local model reproduce TSK's arm effects?** TSK's analysis (H1 to H3, and its secondaries) is run on the local runs, and each effect is shown side by side with the hosted one. For instance: instruction against none on relevant tests, medium against none on passes, gate against instruction.
- The difference between the two models' arm effects, per task. For example, (local medium − local none) − (hosted medium − hosted none).
- Tokens, time, cost, false success claims and failure modes for both models.

**Exploratory:** arm G against arm A (local only): passes, timeouts, time, tokens.

**Analysis code:**
- [`scripts/analyse.py`](scripts/analyse.py) is TSK's, copied with three changes, each marked in the code: arm G added to the arm list; tokens read from the session file when the rig has none; and the tasks folder pointed at TSK's. Run on TSK's published runs, the copy reproduces TSK's `results/analysis.md` byte for byte.
- [`scripts/compare.py`](scripts/compare.py) runs the local-against-hosted comparison with the same loading, permutation test, bootstrap and Holm code (`2026-10-skills-impact/scripts/stats.py`). Run on hosted against hosted, it gives zero differences and reproduces TSK's published effects.

## Before the runs

1. **Tool calling. Done.** A `codex exec` check (read a file, edit it, run a shell command) passed 3 of 3, verified from the session files ([`setup/toolcheck.sh`](setup/toolcheck.sh)).
2. **Isolation. Done** (above).
3. **Smoke test: ADDR, arm A, 1 run. Done twice.** Not part of the results.
   - Run 1 (60-minute limit): the agent made the right fix (two files, as the hosted run did) in its first part, then built and reran a Java harness in `/tmp` until the limit. The grader ran both hidden tests (passed) and the whole existing suite (no failures). Status: timeout. 114 turns, about 2.7M tokens, 84 Wh. The hosted run of the same task took 53 seconds and 0.40M tokens.
   - Run 2 (no time limit, at the user's request): see the amendment log.
   - The shared Maven repository was unchanged after the run (checksum of `com/shopizer`).
4. **Reasoning effort.** Check whether the local server applies Codex's low and medium settings (the reasoning tokens and the thinking output for each). If it does not, arm E repeats arm A in all but name. This is reported as a known limit, and E's comparisons are labelled so.
5. **Hosted calibration.** The rig version differs from TSK's. 20 runs of `gpt-5.6-luna`, arm A, 1 per task, on this machine with this rig, Codex and isolation. Each task's result is compared with TSK's arm A rate. This shows whether the tooling and the platform alone change results. It is descriptive, and does not change the plan.

## Known limits

- One local model, at one quantization (Q4), one context length, and with default sampling.
- **The local agent's tools differ** in three settings (above). Some of any difference may come from the tools, not the model.
- **The time limit hurts a slow model.** The local model is about 30 to 60 times slower per run here. A run that would succeed given more time counts as a failure. Timeouts are reported separately, so their share is visible.
- Runs were made on different dates, platforms and isolation methods. The calibration estimates the effect of all but the model.
- Arm G's wording was chosen after one smoke run.
- The power sensor covers the whole chip, not the GPU alone.
- TSK's own limits apply: one repository, one skill, 20 tasks (able to show a gain of about 15 points, not 10).

## Reproducing

```
# machine set-up (once): setup/sudo-step1.sh, setup/README.md
setup/localize-linux.sh ~/code/experiments/2026-10-test-skill      # trial*.local.toml for the local model
setup/isolation-test.sh ~/code/benchmark/trials/isotest --codex
trialrig run ../2026-10-test-skill/trial.local.toml --out <dir> --agent codex
trialrig run ../2026-10-test-skill/trial-medium.local.toml --out <dir-e> --agent codex
trialrig run ../2026-10-test-skill/trial-gate.local.toml --out <dir-f> --agent codex
trialrig run trial-stop.local.toml --out <dir-g> --agent codex
scripts/export.sh <dir> stage1; scripts/export.sh <dir-e> stage1-medium; scripts/export.sh <dir-f> stage1-gate; scripts/export.sh <dir-g> stage1-stop
python3 -I scripts/analyse.py results/stage1*/runs > results/analysis.md
python3 -I scripts/compare.py > results/compare.md
```

## Amendment log

- 2026-10-23: design written at the user's request ("Do full test run"), after two smoke runs, before any measured run. Arm G added at the user's request ("anything we can add to stop it getting stuck creating the Java harness"; chosen option: keep the limit and add an extra arm). Hosted calibration approved ("go ahead").
