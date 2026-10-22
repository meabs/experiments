# Does a skill add anything to an instruction to test? (Codex)

**Draft design, written 2026-10-22. Not yet run.** Nothing below is fixed until it is committed as final (step 4 of "Before the runs"); after that, changes go in the amendment log at the bottom.

## Why this follows explicit-skills

[2026-10-explicit-skills](../2026-10-explicit-skills/) told the agent to use the repository's skills. It then read the verification skill, `verify-api`, in every run (60 of 60, against 3 of 60 when left to find it). But it mostly did not do what the skill asks.

- The skill says to write a focused integration test of the change. A test of that kind was detected in only 15 and 10 of 60 runs.
- Most runs ran the skill's first example instead: `ActuatorTest`, a smoke test that only checks the application starts.
- The pass rate rose from 37 to 42 and 43 of 60, not significantly.

That leaves two open questions:

1. **Does the skill add anything beyond simply telling the agent to write the test?** The explicit-skills arms combined the skills with an instruction, so their effects cannot be separated.
2. **Was the shortcut caused by the skill's design?** The original skill gives the smoke-test command first, and the advice to write a focused test second.

This design came out of a review of explicit-skills: four arms (A to D) as the review proposed, plus a medium-effort arm (E), a gate that checks the agent's work when it tries to finish (F), and a direct measure of whether the agent's test checks its change.

## Question

When the agent is told to write a focused API test of its change, does giving it the repository's verification skill raise the share of runs that write a test which really checks the change? Does a skill that puts the focused test first do better than the original? And does a gate that checks for such a test when the agent tries to finish do better than telling the agent to write one?

## Agent and repository

- Codex `gpt-5.6-luna` (CLI 0.157), clean home, the same isolation as before. Low reasoning effort, except arm E.
- shopizer at `6a4a0a6` (Java, Maven, JDK 21), offline.

## Arms

| Arm | Name | What the agent gets |
| --- | --- | --- |
| A | `none` | The task prompt only |
| B | `instruction` | The prompt starts with an instruction to write and run a focused API test of the change ([`arms/instruction.md`](arms/instruction.md)). No skill |
| C | `skill` | The same instruction, plus a pointer to the skill ([`arms/instruction-skill.md`](arms/instruction-skill.md)), and the original `verify-api` skill, unedited ([`arms/skill-original`](arms/skill-original/)) |
| D | `skill-revised` | As C, with a revised `verify-api` that puts the focused test first ([`arms/skill-revised`](arms/skill-revised/)) |
| E | `medium` | The task prompt only, at medium reasoning effort |
| F | `gate` | The task prompt only, and a Stop hook that checks for a relevant test when the agent tries to finish, and sends it back once if there is none (below) |

The instruction for B:

> Before you say you are done, add a focused test that checks your change through the API, calling the endpoint the way a client would, and run it. It should fail without your change and pass with it.

C and D add one sentence: "Read and follow .agents/skills/verify-api/SKILL.md, which explains how to do this in this repository." The pointer is needed: left to discover it, the agent opened this skill in 3 of 60 runs. So "the skill" here means the skill and a pointer to it.

No arm has `AGENTS.md` or the other two skills (`safe-change`, `build-test`). The only guidance that differs between B, C and D is the verification skill.

### The gate (arm F)

Codex runs hooks: commands it calls at fixed points. A *Stop hook* runs when the agent tries to finish, and can block that and send the agent back with a reason. Arm F's hook ([`scripts/gate.sh`](scripts/gate.sh)) runs the same relevance check the grader uses (below), on the agent's clone. It never reads the hidden tests.

- **If the change has a relevant test,** the agent finishes.
- **If not,** the finish is blocked once, and the agent is told the result, with no advice on how to fix it:

  | result | what the agent is told |
  | --- | --- |
  | no test of its own | "Before you finish: no test of your own was found in your change. Add a test that checks your change through the API, and run it. It should fail without your change and pass with it." |
  | its tests fail with the change | "Before you finish: your tests fail with the change: (the failing tests). Make them pass." |
  | its tests also pass on the original | "Before you finish: your tests also pass on the original code, so none of them checks your change. Add a test that fails without your change and passes with it." |
  | its tests do not compile or run | "Before you finish: your tests did not compile or run with your change. Make them run and pass." |

- **At most once.** On the second attempt to finish, the hook checks again and records the result, but always lets the agent finish.
- **How it is set up.** The hook lives in arm F's own clean home (`scripts/make_gate_home.sh`), because the rig hides the experiments folder from the agent. Codex asks a person to approve new hooks; arm F passes `--dangerously-bypass-hook-trust` so this one runs without that. Each check is saved in the clone's `.git` folder, and the grader copies it to the run's results.
- **The gate gives no how.** It tells the agent what failed, not how to write a test in this repository. So it tests checking the agent's work, not guidance.

### The revised skill

The revision only reorders and rewords the original. It adds no knowledge of the tasks.

- **First:** write a focused test calling the changed endpoint, which should fail without the change and pass with it. The command to run it uses `<YourTestClass>`.
- **Then:** `ActuatorTest` as the pattern to copy, with the note that it only checks the application starts, so running it does not verify a change.
- **Unchanged:** why the application cannot be started on its own here.

The full difference is in `diff arms/skill-original arms/skill-revised`.

## Tasks

The 20 tasks of verify-vs-skills, repo-skills and explicit-skills, unchanged. That keeps the results comparable with the last three experiments.

On pass rate, half of them do not discriminate: in explicit-skills, every arm passed 8 of them in every run and failed 2 every time. That is one reason pass rate is secondary here.

## Size and cost

20 tasks × 6 arms × 3 runs = **360 runs**. At explicit-skills' costs, this is about $10 to $16. Each run's grading also runs the relevance check, about a minute.

Arms E and F each run in their own trial file, alongside A to D: the rig cannot set effort per arm, and F needs its own home for the hook (`trial-medium.toml`, `trial-gate.toml`).

## Measures

**Primary: a relevant test.** A run has one if both of these hold:

- the agent added or changed at least one test, outside the hidden tests, and all of them pass with its change;
- at least one of them fails on the original code.

The grader checks this automatically ([`scripts/relevance.sh`](scripts/relevance.sh)), before it adds the hidden tests:

1. It finds the test files the agent added or changed, and runs the test classes among them with the agent's change.
2. It exports the original code, copies the agent's test files in, and runs them again.

A test that does not compile against the original code counts as failing there, and these runs are reported separately. This replaces explicit-skills' proxy, which looked for an added line with `TestRestTemplate` and similar names.

**Secondary:**

- **Verified pass:** the build ran, every hidden test ran and passed, and no existing test failed, as before.
- **Wrote any test**, **ran its own test**, **ran only `ActuatorTest`**, **read the skill**: from the commands the agent ran.
- **Cost** per verified pass and per relevant test, tokens and time.
- **Arm F only:** how often the gate blocked, why, and whether the second check found a relevant test.
- **False success claims.**

## Hypotheses and analysis (to be fixed before the runs)

The unit is the task. For each task and arm, the result is the number of runs, out of 3, with a relevant test.

| # | Hypothesis | Test |
| --- | --- | --- |
| H1 | `skill` gives more relevant tests than `instruction`: the skill adds something beyond the instruction | One-sided exact sign-flip permutation test over the 20 tasks |
| H2 | `skill-revised` gives more relevant tests than `skill`: the skill's design matters | As H1 |
| H3 | `gate` gives more relevant tests than `instruction`: checking the work beats telling the agent | As H1 |

- H1 to H3 are Holm-adjusted together at α = 0.05.
- **Secondary**, reported but not tested as hypotheses:
  - relevant tests in `instruction` against `none`;
  - pass rate of every arm against `none`, two-sided, unadjusted, with bootstrap intervals over tasks.
  - **Pass rate is underpowered here.** In explicit-skills, the spread of per-task differences means detecting a 10-point gain needs about 70 tasks, and a 15-point gain about 30 (80% power, one-sided α = 0.05, 3 runs per task). This experiment can show changes in behaviour; it cannot settle small changes in pass rate.
  - `medium` against the best guided arm, on pass rate and cost per verified pass. This compares thinking longer with being told, in the same hours.
  - `gate` against `instruction` on pass rate, two-sided: whether checking the work changes correctness, not only tests.
- **Exploratory:** the pass rate of runs with and without a relevant test, in each arm. This is not causal.

## Before the runs

1. **Check the hook works under the rig. Done.**
   - Outside the rig, under `codex exec`, a Stop hook blocked once, the agent followed the reason, and the second stop was let through (`stop_hook_active`).
   - Through the rig, arm F was run on SUPERDEL, then on SUPERDEL and TAXRATE. These runs are not part of the results.
   - The first test run found a fault: the gate passed its log folder as a relative path, so the run on the original code could not write its log. The check then read "no result" as "passes on the original".
   - Both are fixed. The gate now uses absolute paths. A check that cannot run is recorded as a "check error", and it never blocks the agent or counts as a verdict.
   - In the last test runs, the gate blocked each run once ("no test of its own"). Each agent then wrote a test, and the second check found it relevant, in 41 and 67 seconds. The gate's verdict matched the grader's in both runs. One of the two still failed the hidden tests: a relevant test does not make the change correct.
2. **Build the relevance check and validate it on explicit-skills' runs. Done.**
   - The 27 runs that changed a test file (16 told in the prompt, 11 told in `AGENTS.md`) were rebuilt from their saved diffs ([`scripts/retro.sh`](scripts/retro.sh)) and checked.
   - **All 27 have a relevant test:** every test passes with the change, and at least one fails on the original code. None relied on the original failing to compile. Results are in [`results/retro-explicit-skills`](results/retro-explicit-skills/).
   - So explicit-skills' diff-based proxy (15 and 10 runs) slightly undercounted. Two runs, one per arm, on CARTCALC, wrote relevant tests it did not detect. Every test it did detect was relevant.
   - Of these runs, 14 of 16 and 10 of 11 passed the hidden tests.
3. **Write `scripts/analyse.py` and check it. Done.** It was run on explicit-skills' runs, with arms renamed and the relevance results above, and on the gate test runs. All sections ran.
4. **Commit the design as final, then run.**

## Known limits

- One repository, one agent, one model, and one verification skill, revised by me. The revision is a reordering, not new knowledge, but I know the tasks.
- B, C and D are all told to write a test. This experiment asks what helps the agent carry that out, not whether it should be told.
- Arms E and F run in their own trial files, alongside A to D but not interleaved with them.
- **The gate can be gamed.** A test that fails on the original only because it does not compile there passes the gate. The grader decides independently, with the hidden tests, and such runs are reported separately.
- **The agent can see the gate.** Its scripts are in arm F's home folder, which the agent could read or change. Any run that touches them is reported.
- **The gate adds time and tokens.** Each check runs Maven twice, 40 to 70 seconds in the test runs. A blocked run then does more work: the two test runs used about 1.9M tokens each, against about 1M for the told arms of explicit-skills. The time limit for arm F is 45 minutes.
- The relevance check shows that a test distinguishes the change from the original, not that it tests the behaviour the task asked for.

## Reproducing

```
python3 -I scripts/make_trial.py && scripts/localize.sh
scripts/make_gate_home.sh ~/code/benchmark/skills-impact-work      # arm F's home, with the Stop hook
trialrig run trial.local.toml --out <dir> --agent codex
trialrig run trial-medium.local.toml --out <dir-e> --agent codex
trialrig run trial-gate.local.toml --out <dir-f> --agent codex
scripts/export.sh <dir> stage1; scripts/export.sh <dir-e> stage1-medium; scripts/export.sh <dir-f> stage1-gate
python3 -I scripts/analyse.py results/stage1/runs results/stage1-medium/runs results/stage1-gate/runs > results/analysis.md
```

## Amendment log

- 2026-10-22: draft written at the user's request, from a review of explicit-skills. It uses the review's four arms, plus medium effort and the relevance measure.
- 2026-10-22 (draft, before any run): arm F (Stop-hook gate) and H3 added at the user's request ("Is it worth adding any hooks" … "Do it").
