# Is a code guide worth more to a small local model? (OKF test G, qwen3.8:27b)

**Final design, committed 2026-10-27 before any measured run.** Later changes go in the amendment log at the bottom.

## Why

The [OKFExperiment](https://github.com/meabs/OKFExperiment) tests found one idea behind every result: **a guide is a substitute for reading the code.** It helped exactly when the agent could not read the code, and added nothing (or cost a little) when it could. In test G, four storefront changes that each depend on facts stated only in the backend, the hosted model passed:

| What the agent had (OKF test G, `gpt-5.6-luna`, 5 runs per task) | Changes that passed (of 20, higher is better) |
| --- | --- |
| No guide (backend not available) | 3 |
| The backend's source, readable | 18 |
| The backend's OKF guide | 18 |

So for the hosted model, the guide and the source were worth the same.

A small local model reads code at a very different price. `qwen3.8:27b` on this machine has a 65,536-token context (the hosted model has 272,000), and in [test-skill-local](../2026-10-test-skill-local/) it was 30 to 60 times slower per run. Reading a 1,173-file Java backend to find six field names should cost it far more than reading a compact guide. If reading is the bottleneck, **the guide should beat the source for the local model**, which it did not for the hosted model. If the guide and the source still tie, OKF's explanation holds for small models as well. Either result is worth reporting.

## Question

On OKF test G's four tasks, with Codex running the local `qwen3.8:27b`:

1. Does the backend's guide raise verified passes over no guide, as it did for the hosted model?
2. Does the guide beat the backend's source, which it did not for the hosted model?
3. Does the guide make runs faster or cheaper in energy than the source?

The hosted results are not rerun. They come from OKFExperiment's [`results/G-harder-crossrepo-change-tasks.md`](https://github.com/meabs/OKFExperiment/blob/5a090274481d1386ed96e75fa2a90d47c2d4a7c4/results/G-harder-crossrepo-change-tasks.md) at commit `5a09027`.

## Agent and repositories

- **Agent:** Codex CLI 0.157.0 with `qwen3.8:27b` (Q4_K_M, Ollama 0.40.5 on ROCm, context 65,536), reasoning effort `medium` as in test G. The set-up, and how its tools differ from the hosted Codex, is in [test-skill-local](../2026-10-test-skill-local/README.md#agent-and-repository) and `~/code/benchmark/local-setup/README.md`.
- **Isolation:** bubblewrap ([`setup/codex-bwrap.sh`](setup/codex-bwrap.sh)): `/home` is empty apart from this run's workspace, so the hidden tests, the guides of other arms and every other run are invisible. The `source` arm alone gets the backend bound in read-only at its own path (`CODEX_RO_BIND`, the only change to the wrapper).
- **Workspace (all arms):** the Shopizer React storefront at `455b4bc`.
- **Backend:** Shopizer at `6a4a0a6`, with OKF's renames applied (`scripts/privatize.py`, then `--extra`, from OKFExperiment), so no field can be answered from memory. This is test G's backend.
- **Guides:** generated with `kgen` (AgentGraphWorkTree at `aa98666`, the commit OKF names), `--preset recommended`: the backend's guide, mirrored under the storefront guide's `okf/references/backend/`. Both pass OKF's `check_okf.py` with no findings. The code graphs `kgen sync` writes into a repository (`.agent-knowledge/`) are moved out before any run, so no arm sees one.

## Arms

Copied from OKF test G ([`make_g.py`](https://github.com/meabs/OKFExperiment/blob/5a090274481d1386ed96e75fa2a90d47c2d4a7c4/scripts/make_g.py)); each arm is an `AGENTS.md` (and for `okf`, the guide) laid over the storefront.

| Arm | What the agent has |
| --- | --- |
| `no_okf` | The storefront only. `AGENTS.md`: the backend is a separate repository and is not available. |
| `okf` | The storefront with its guide in `okf/`, the backend's guide in `okf/references/backend/`, and OKF's pointer text ("Use it to find your way around, then read the source to confirm before you rely on it"). |
| `source` | The storefront, and the renamed backend's source, read-only, at the path `AGENTS.md` gives. |

Test G's fourth arm, the guide with confidence labels, is left out: labels made no difference in G (17 against 18 of 20), and the time is better spent on runs.

## Tasks

Test G's four, prompts unchanged, each with a hidden test that runs the storefront's own modules in plain Node with the network and browser stubbed ([`harness/`](harness/), [`hidden/g/`](hidden/g/), [`scripts/verify_g.sh`](scripts/verify_g.sh), copied from OKFExperiment):

1. **Fix `deleteFromCart`:** it sends the cart line's id, but the backend identifies the line by its SKU.
2. **Add an optional discount code to `addToCart`,** in the backend's field name.
3. **Write a checkout request builder:** six fields renamed in the backend, some in parent classes, and two classes called `PersistableOrder`.
4. **Write an order-list reader:** paging fields defined in a parent list class.

The prompt ends with test G's suffix: "Say briefly which files you used." Checked before the runs: every hidden test fails on the untouched storefront and passes on OKF's reference solution (`solve_g.py`).

## Size and cost

- **3 arms × 4 tasks × 5 runs = 60 runs,** as many per task as test G. From the smoke test (about 4.5 to 7 minutes a run), about 6 to 7 hours: one night.
- **Order:** one repetition at a time, the three arms in a rotating order, so a slow night or a warm cache does not favour one arm.
- **Time limit per run: 1,200 s,** as test G. A run that reaches it is graded on what it left, and counts as a failure; timeouts are reported separately.
- **No API bill.** Energy from APU package power ([`setup/powerlog.sh`](../2026-10-test-skill-local/setup/powerlog.sh)), at 0.25 £/kWh.

## Measures

- **Verified pass (primary):** the hidden test passed, and the run finished (status `ok`).
- **Correct but timed out:** the hidden test passed on what a timed-out run left. Reported, not counted as a pass.
- **Wall time** per run, **tokens** (from the Codex session file), **turns**, **energy** per run.
- **Used the arm:** the rig's `uses` check (a tool call touching `okf/`, or the backend's path).
- **Left the workspace:** any tool call reading outside the workspace (and, for `source`, the backend). OKF's `leak_check.py` idea, on the session files.
- **What it read:** for `okf` and `source`, how many guide or backend files each run opened.

## Hypotheses and analysis (fixed before the runs)

Arms are compared by the mean, over the four tasks, of each task's pass rate, so every task counts equally.

| # | Hypothesis | Test |
| --- | --- | --- |
| H1 | `okf` passes more than `no_okf` | One-sided permutation test, arm labels shuffled within each task |
| H2 | `okf` passes more than `source`: the guide is worth more than the code to a small model | As H1 |
| H3 | `okf` runs take less wall time than `source` | One-sided permutation test on per-task mean wall time, labels shuffled within each task |

- 100,000 random shuffles (seed 1). Effect intervals: bootstrap within tasks, 10,000 resamples (seed 1). H1 to H3 Holm-adjusted together at α = 0.05. Script: [`scripts/analyse.py`](scripts/analyse.py).
- **How to read them, fixed now:**
  - **H1** confirmed: the guide's value carries over to a small local model.
  - **H2** confirmed: a new result; for a small model the guide beats the code it describes. Not confirmed: the guide is no better than the source, as for the hosted model ("no measurable difference" means just that).
  - **H3:** if H2 is not confirmed but H3 is, the guide still buys speed.
- **Secondary,** reported but not tested: `source` against `no_okf`; energy and tokens per arm; timeouts; local against hosted, per arm and task, side by side (the hosted runs are 5 per task; no test, as the platforms, rigs and dates differ).
- **The arm didn't happen as designed** if fewer than three quarters of `okf` runs opened the guide, or of `source` runs read the backend. That is reported instead of a verdict on the hypotheses that use the arm.
- **Power.** Four tasks and a few runs each can show only large differences. Hosted test G separated 3/20 from 18/20 at p < 0.001; a gap of a few runs between `okf` and `source` will show as "no measurable difference".

## Before the runs

1. **Grader check. Done.** All four hidden tests fail on the untouched storefront and pass on OKF's reference solution.
2. **Smoke test. Done** (not counted): task 2 (discount code) once in each arm.

   | Arm | Hidden test (pass is better) | Wall time (lower is better) | Tokens (lower is better) | Turns | Used the arm |
   | --- | --- | --- | --- | --- | --- |
   | `no_okf` | failed | 4.6 min | 251k | 15 | (no guide or backend) |
   | `okf` | passed | 6.9 min | 759k | 30 | opened the guide |
   | `source` | passed | 6.9 min | 736k | 43 | read the backend |

   - Isolation, from the session output: the `okf` and `no_okf` runs never named the backend's path, and no run named the experiments folder (where the hidden tests are). Only `source` read the backend.
   - The hosted run of the same task took about 40 s and 240k to 380k tokens; the local model is about 10 times slower here, far less than the 30 to 60 times in test-skill-local's Java tasks.
   - From this, N = 5 (above).
3. **Analysis script run on the smoke runs. Done:** every section ran ([`scripts/analyse.py`](scripts/analyse.py)).
4. **Design committed as final and pushed, then run** overnight, with the user's go-ahead: "Have it run overnight" and "Just start when yiu are ready".

## Known limits

- One local model, one quantization, one context length, default sampling. The local agent's tools differ from the hosted Codex in three settings ([test-skill-local](../2026-10-test-skill-local/README.md)).
- Four tasks, from one storefront and one backend; the backend's names are renamed by hand.
- The guide was regenerated here with the generator commit OKF names; it may differ in small ways from the copy test G used, which is not in OKFExperiment.
- The hosted comparison is across platforms (macOS and Linux), isolation methods and rig versions.
- A time limit hurts a slow model; timeouts are reported separately so their share is visible.

## Reproducing

```
setup/build.sh                                     # workspaces and guides, in ~/code/benchmark/okf-local
python3 scripts/make_trial.py                      # overlays and trial-<arm>.local.toml
scripts/run_all.sh <out dir> 5                     # one repetition at a time, rotating the arms
python3 -I scripts/analyse.py <out dir> > results/analysis.md
```

## Amendment log

- 2026-10-27, 22:30: design committed as final and pushed; the measured runs start straight after (the user: "Just start when yiu are ready").
