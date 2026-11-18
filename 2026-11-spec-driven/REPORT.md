# Do spec-driven toolkits help a coding agent fix hard bugs? Report (experiment SDD)

*Site title: Does a spec-driven workflow beat good practice on hard bug tickets? (SDD)*

**This experiment was designed and run with an AI agent** (Claude Code, working for me): it drafted the design, wrote
the long AGENTS.md for arm L and the prompt wording for arms R, S and O, installed the two toolkits and ran the
analysis. I chose the arms and approved the design and the run. Arm L's text is the agent's, not a real project's.

18 November 2026. Design: [README.md](README.md), written before any measured run (a one-ticket pilot, one run per
arm, checked the installs and the wording; it is not in the results). Full numbers:
[results/main/analysis.json](results/main/analysis.json), per run [results/main/runs.csv](results/main/runs.csv),
every final message [results/main/answers.json](results/main/answers.json).

## 1. What I wanted to find out

Spec Kit, OpenSpec and "research, plan, implement" are the most-adopted ways of giving a coding agent a process. I
wanted to know whether they help a Codex agent on hard, real bug reports, compared with no setup and with the six-line
disciplined setup (D) from my earlier experiment ELC. I also wanted to know whether a long AGENTS.md does worse than a
short one, as the "keep it under 100 lines" advice says.

## 2. What I predicted

Written before the runs (README section 6):

- H1 to H3: Spec Kit's bug-fixing skills (S), OpenSpec (O) and research-plan-implement (R) each pass more hidden tests
  than no setup (V).
- H4: no process arm (R, S or O) passes more than D.
- H5: the long AGENTS.md (L) passes fewer than D.

## 3. How I tested it

Six hard Shopizer bug reports from ELC (a Java online shop; each has hidden, interacting causes and hidden acceptance
tests), the same agent for every run: Codex CLI 0.157 with gpt-5.6-luna (hosted) at medium effort, one turn, bubblewrap
sandbox, no one to ask. Six arms, 5 runs per ticket and arm, 6 x 6 x 5 = 180 runs. Every run starts from a fresh clone.

| Arm | What the agent got |
| --- | --- |
| V | Shopizer as it is |
| D | ELC's disciplined setup: six AGENTS.md lines and three small skills (copied unchanged) |
| L | D's six lines plus about 125 lines of ordinary reference notes (134 in all); D's skills kept |
| R | research, then plan, then implement, asked for in the prompt, with notes written to `notes/` |
| S | Spec Kit 1.4.2 bug-fixing skills (`$speckit-bug-assess`, `-bug-fix`, `-bug-test`), run in order in automated mode |
| O | OpenSpec 2.1.0 skills (`$openspec-propose`, `-apply-change`, `-archive-change`), run in order |

S and O were run without the human review they are designed around: a single turn has nobody to review each step.
That affects every claim about them below.

Measure: the share of the ticket's hidden tests passed per run (a run that doesn't compile scores 0; all 180
compiled), averaged over each ticket's runs and then over the six tickets. Tests: one-sided permutation within ticket
(100,000 shuffles, seed 1), bootstrap 95% intervals within ticket, Holm correction within each hypothesis group
(`scripts/analyse.py`). All 180 runs finished with status ok; one S run that lost its connection was re-run.

## 4. What happened

### Headline

None of the three process arms did better than no setup, and all three did worse than the six-line setup.

| Arm | Hidden tests passed | Runs passing every test | Cost per run (list price) | Cost per hidden test passed |
| --- | --- | --- | --- | --- |
| V (none) | 42.3% | 1 of 30 | $0.063 | $0.0128 |
| D (disciplined) | 53.5% | 2 of 30 | $0.115 | $0.0187 |
| L (long AGENTS.md) | 52.8% | 3 of 30 | $0.107 | $0.0175 |
| R (research, plan) | 42.6% | 1 of 30 | $0.098 | $0.0199 |
| S (Spec Kit) | 40.7% | 1 of 30 | $0.106 | $0.0228 |
| O (OpenSpec) | 38.2% | 0 of 30 | $0.112 | $0.0257 |

The whole experiment cost about $18 at list price ($0.20, $0.02 and $1.20 per million input, cached and output
tokens), the same prices as ELC.

### Hypotheses

| | Comparison | Difference | 95% interval | p (one-sided) | Holm p | Result |
| --- | --- | --- | --- | --- | --- | --- |
| H1 | S minus V | -1.6 points | -11.3 to +8.0 | 0.61 | 1.00 | not supported |
| H2 | O minus V | -4.2 | -14.9 to +5.8 | 0.75 | 1.00 | not supported |
| H3 | R minus V | +0.3 | -10.7 to +11.1 | 0.48 | 1.00 | not supported |
| H4 | R minus D | -10.9 | -20.5 to -0.9 | 0.97 | 1.00 | holds: R does not beat D |
| H4 | S minus D | -12.8 | -21.3 to -3.6 | 0.99 | 1.00 | holds |
| H4 | O minus D | -15.3 | -24.6 to -5.8 | 1.00 | 1.00 | holds |
| H5 | D minus L | +0.7 | -9.6 to +10.7 | 0.45 | 0.45 | not supported: L is no worse than D |

The intervals for R, S and O against D exclude zero, but only the "does not beat" direction was pre-registered, so the
"worse than D" reading is exploratory.

Two comparisons I added afterwards, both exploratory: D minus V is +11.1 points (interval +0.1 to +21.4, p 0.033, Holm
0.065 over the two), and L minus V is +10.4 (-0.7 to +21.2, p 0.046, Holm 0.065). Same direction as ELC's round 1
(+17 for D), but after correction neither is clearly different from no setup.

### Per ticket

Mean share of hidden tests passed, five runs each:

| Ticket | V | D | L | R | S | O |
| --- | --- | --- | --- | --- | --- | --- |
| CATEGORYDELETE | 44% | 53% | 62% | 58% | 67% | 60% |
| CUSTOMERCART | 22% | 22% | 20% | 18% | 20% | 22% |
| PRODUCTDELETE | 42% | 62% | 64% | 40% | 9% | 9% |
| REVIEWS | 24% | 54% | 34% | 20% | 32% | 34% |
| STOCK | 52% | 60% | 67% | 55% | 47% | 51% |
| SUPPORTORDERS | 70% | 70% | 70% | 65% | 70% | 53% |

PRODUCTDELETE is all or nothing: a run either finds the hidden cause (9 to 11 of 11 tests) or passes 1 of 11. Runs
that found it: V 2 of 5, D 2 of 5 (plus two partial at 6), L 2 of 5 (two partial), R 2 of 5, S 0 of 5, O 0 of 5. That one
ticket accounts for all of S's and O's gap to V (without it, O would be about 2 points and S about 5 points ahead of V, still within noise), and it is five runs per cell.

### What each process arm did

The skills were used. Counted from the files each agent left in its change, not from its summary:

- R: all 30 runs wrote `notes/research.md` and `notes/plan.md`.
- S: all 30 runs wrote the three Spec Kit reports (assessment, fix, test).
- O: all 30 runs created an OpenSpec change. None stopped after the plan.

So the lack of a gain is not because the process was skipped.

They changed more files and spent more: the mean number of files changed per run was 5.9 (V), 6.6 (D), 6.8 (L), 8.3 (R), 9.6 (S)
and 11.6 (O). Every setup roughly doubled the tokens: 1.9M per run for V against 3.1M to 3.7M for the others.

### Do the summaries tell the truth?

Of the runs that missed hidden tests, the final message said done and passed (and admitted nothing unfinished) in 27 of
29 (V), 28 of 28 (D), 26 of 27 (L), 29 of 29 (R) and 28 of 30 (O). S was different: 13 of 29. In 11 of S's 29 failing
runs the agent's own VERIFICATION line said "partial" and named what it could not verify (for example "Live HTTP, cart
and order flows"), against none of V's, D's or R's. The Spec Kit test step seems to make the agent say what it did not
check. It did not make it fix more.

## 5. What surprised me

- **A process built for exactly this didn't help.** Spec Kit's bug-fixing skills are made for "assess, fix, verify",
  and the agent followed them every time, and got no more tests right than with nothing.
- **The long file did no harm.** 134 lines against 9 made no measurable difference.
- **Spec Kit made the agent more honest without making it more right.** It was the only arm whose summaries often
  said "partial".
- **OpenSpec produced the biggest changes** (11.6 files per run) and the lowest score.

## 6. What this might mean in practice

I'd treat these as leads, not rules: one repository, one model, five runs per ticket.

- On hard bug tickets, a short, general checklist (D) did better than heavier processes. The process arms added cost
  (about 1.5 to 2 times V's per run) and no measurable gain.
- If you use a spec toolkit, don't expect it to find hidden causes. It may make the agent more candid about what it
  didn't check.
- Length of an instruction file isn't, on this evidence, the thing to worry about.

## 7. What the experiment does not prove

- S and O were run unattended, one turn. A person reviewing each step is how they're meant to be used, and this says
  nothing about that.
- Spec Kit's feature flow (`/speckit-specify`, `-plan`, `-tasks`, `-implement`) was not tested, only its bug-fixing
  extension.
- One repository, one agent (Codex CLI 0.157), one model (gpt-5.6-luna), medium effort, single turn.
- Arm L is one long file written by the agent. Other long files may differ.
- Five runs per ticket and arm; "no measurable difference" is not "the same". A larger round could show a gain or a
  loss, especially on PRODUCTDELETE, where results are all or nothing.
- The false-claim count is a mechanical rule on the final message (the VERIFICATION line says "passed" and nothing
  unfinished is admitted); it measures what the agent said, not what it knew.
- Hidden tests measure these tickets' behaviour, not code quality.
- Tickets, hidden tests and D are the same as in ELC round 1, so D's number here is a repeat on the same six tickets,
  not an independent set.

## 8. What I'd test next

- Run S and O with a scripted reviewer that answers their questions, to see whether the human-in-the-loop version
  helps.
- Test Spec Kit's feature flow on feature work instead of bugs.
- Add held-out tickets, so the bimodal PRODUCTDELETE pattern doesn't dominate.
- Try the Spec Kit "partial" effect on its own: ask D's agent to list what it could not verify, and see whether summaries
  get more honest without the toolkit's cost.

## 9. How to reproduce the results

```sh
bash scripts/make_arms.sh                       # once, needs network: Spec Kit and OpenSpec files, the openspec command
python3 -I scripts/make_trial.py                # writes trial-{V,D,L,R,S,O}.local.toml
# from the AgentTrialRig checkout, with the hosted Codex profile set up
uv run trialrig run <path>/trial-V.local.toml --agent codex --out <path>/results/main/V   # and D, L, R, S, O
python3 -I scripts/analyse.py                   # writes results/main/analysis.json, runs.csv, answers.json
```

## 10. What changed from the design

- Arm L is 134 lines, not about 250 (README section 3, amendment of 18 November).
- The rig takes one prompt suffix per trial, not per arm, so each arm's suffix is written into its tickets' prompts.
- Holm correction is applied within each hypothesis group (H1 to H3 together; H4's three comparisons together; H5
  alone), where the README said H4 and H5 are "tested separately".
- D minus V and L minus V were added as exploratory comparisons.
- The run was stopped part-way when my hosted-model credits ran out and resumed later. Runs that were in flight at the
  stop have no result file and were run again from scratch. No finished run was discarded or re-run. One S run that
  lost its connection (a "stream disconnected" error) was re-run by the retry pass.
- My first count of R's use of its notes files read only shell commands and said 10 of 30; counting files in the change
  gives 30 of 30. The report uses the second count.
