# Does a spec-driven workflow beat good practice on hard bug tickets? (experiment SDD)

Status: main run done (180 Codex runs, 18 November 2026); see [REPORT.md](REPORT.md). This design was written before any measured run; amendments are in section 10.

## 1. Question

Spec Kit, OpenSpec and "research, plan, implement" are the most-adopted ways of giving a coding agent a process. Do they raise the share of hidden acceptance tests a Codex agent passes on hard, real bug reports, compared with no setup and with the six-line disciplined setup from ELC (arm D)? And does a long AGENTS.md do worse than a short one, as the "keep it under 100 lines" advice says?

## 2. Why it is worth testing

- Popularity is not evidence. Every source found while preparing this was a directory, a vendor blog or a README; none measured an outcome.
- ELC round 1 found the six-line setup (D) beat no setup by 17 points, and a setup built from many findings (E) did no better than none. That points to "less, but the right things". These arms test whether heavier process helps or hurts.
- One published study (Evaluating AGENTS.md, arXiv 2602.11988) found context files gave no gain and cost over 20% more, on SWE-bench Lite and a Python benchmark. This tests the same question on Java, with hidden behavioural tests, and adds process toolkits.

## 3. What is being changed: the arms

Same agent, model, repository commit and tickets in every arm. One variable per arm, compared with V (baseline) and with D.

| Arm | What the agent gets | Built from |
| --- | --- | --- |
| V | Shopizer as it is | nothing added |
| D | ELC's six-line AGENTS.md and three small skills | copied unchanged from `2026-11-evidence-led/arms/D` |
| L | D's six lines padded to 134 lines with ordinary advice (repository overview, build and test commands, style, design, persistence, errors, testing, security, ticket handling); D's three skills are kept, so L differs from D only in the AGENTS.md | written once, frozen before runs; none of it contradicts D |
| R | Research, plan, implement: the prompt asks for a written research note, then a written plan, then the change, all in one turn | a suffix written into each ticket's prompt (`arms/R/suffix.md`), no files added |
| S | Spec Kit with its bug-fixing extension: `/speckit-bug-assess`, `-bug-fix`, `-bug-test`, installed with `specify init` for Codex | installed in `prepare`/`setup`; the prompt tells the agent to run those three skills in order without stopping for review |
| O | OpenSpec default profile: `/openspec-propose`, then `/openspec-apply-change`, then `/openspec-archive-change` (Codex form: `$openspec-propose`) | installed in `prepare`/`setup` with `openspec init`; same no-stopping instruction |

Notes on S and O:

- Both are designed for a person to review each step. A single `codex exec` turn has nobody to review, so these arms test the toolkit's files and procedure run end to end, not the toolkit as a team would use it. This goes in the limits of every finding about S and O.
- Both need the toolkit installed with network access, then a sandbox with none. Install in `prepare` (once), copy the generated files into each clone, and check in the first dry run that no run needs the network.
- Each arm's exact files and the exact prompt sent are saved with every run (`prompt.txt`, `run.json`). Skill use is counted from tool calls (`uses` regex), not from the agent's summary.

Install check (done in a throwaway directory, 18 Nov 2026, no runs):

- Spec Kit `specify-cli` 1.4.2: `specify init --here --force --non-interactive --integration codex --integration-options="--skills"`, then `specify extension add bug`. Puts skills in `.agents/skills/` (`speckit-bug-assess`, `-bug-fix`, `-bug-test`, plus the feature skills) and scripts in `.specify/`; 484 KB. Codex form is `$speckit-bug-assess`. The skills have an "automated mode" (no questions asked, refuse rather than guess), which is what an unattended run needs.
- OpenSpec 2.1.0: `openspec init --tools codex --scope project`. Puts six skills in `.agents/skills/` and `openspec/` (config, specs, changes); Codex form is `$openspec-propose`. The skills call the `openspec` CLI, so it must be on the agent's PATH inside the sandbox (install into a prefix in `prepare`).
- Each skill is 190 to 260 lines, so arms S and O add a lot of text to the agent's context; that is part of what is being tested.
- `openspec-propose` has an explicit planning boundary: it creates the plan and must stop, and implementation needs a separate user request. A single turn cannot honour both, so arm O's prompt has to ask for propose, then apply, then archive as three named steps in one turn. The agent may still stop after the plan; the number of O runs that never reached apply is a result, counted from tool calls and files written.
- Spec Kit's bug skills assume a bug slug and a report; arm S's prompt supplies the ticket text as the bug report and says to use automated mode.

Pinned versions: specify-cli 1.4.2, OpenSpec 2.1.0. Both need network to install and none after, so install in `prepare` and copy in.

## 4. The tickets

The six hard Shopizer tickets from ELC round 1 (CATEGORYDELETE, CUSTOMERCART, PRODUCTDELETE, REVIEWS, STOCK, SUPPORTORDERS) at `6a4a0a6`, with the same hidden tests and `verify.sh`, so results compare directly with ELC.

ELC round 2 tickets are held out for ELC-H1 and are not used here.

Because ELC's V and D arms were already run, they are re-run here at the same time as the new arms, not borrowed: model behaviour and the rig can change between weeks.

## 5. Measures

- Primary: mean share of hidden acceptance tests passed per run, each ticket counted equally (same as ELC).
- Runs that passed every hidden test.
- Cost per run at list price, tokens, wall time, and cost per fully passing run.
- Process used: counted from tool calls and files written (spec or plan files created, toolkit skills opened, tests written). Not taken from the agent's summary.
- False success claims: of runs that missed hidden tests, how many said they were done (same as ELC-3).

## 6. Hypotheses and analysis

Pre-registered, directional, tested against V unless stated. Holm correction across the five arm comparisons for H1 to H3; H4 and H5 are tested separately.

- H1: S passes more hidden tests than V.
- H2: O passes more hidden tests than V.
- H3: R passes more hidden tests than V.
- H4: no process arm (R, S or O) passes more than D. Written this way because ELC suggests the short setup is hard to beat.
- H5: L passes fewer hidden tests than D.

Analysis follows ELC: paired by ticket, 95% intervals on the difference in mean share, Holm-adjusted p. "No measurable difference" is reported when the adjusted test finds none, even if the raw interval excludes zero. Anything beyond H1 to H5 is labelled exploratory.

## 7. Size, cost and time (estimate)

6 tickets x 6 arms x 5 runs = 180 runs, after a one-ticket dry run of every arm to confirm installs, offline operation and prompt wording.

ELC cost was about $0.065 per run for V and $0.121 for D. The process arms are likely to cost several times that. Rough guess $20 to $40 in total; to be replaced by measured pilot cost before the main run. Sequential time at ELC speeds is long, so run with `parallel` as in ELC if the machine allows.

## 8. Rounds

One round. If a process arm clearly helps, a second round could add held-out tickets and a human-in-the-loop version of S or O (a scripted reviewer that answers the toolkit's questions).

## 9. Limits known in advance

- One repository, one agent (Codex CLI), one model (gpt-5.6-luna) at medium effort, one turn per run.
- S and O are run without the human review they are designed around (section 3). A null result for them is a result about unattended single-turn use only.
- L is one particular long file, not all long files. Its length and content are chosen by me.
- The bug-fixing extension of Spec Kit is not its main feature flow (`/speckit-specify`, `-plan`, `-tasks`, `-implement`); this test does not cover the feature flow.
- Hidden tests measure these tickets' behaviour, not code quality or maintainability.
- Toolkit versions change quickly; results apply to the pinned versions.

## 10. Amendment log

- 18 Nov 2026, before any run: L is 134 lines, not about 250 (section 3 corrected). The rig's `prompt_suffix` is per trial, not per arm, so each arm's suffix is written into its tickets' prompts, as ELC writes its header. Arm O uses a copy of the shared sandbox script with the PATH extended (`build/codex-bwrap-sdd.sh`, made by `scripts/make_arms.sh`).

How to run: run `bash scripts/make_arms.sh` once, `python3 -I scripts/make_trial.py [--pilot V,D,L,R,S,O --tasks CATEGORYDELETE --reps 1]`, then from the AgentTrialRig folder `uv run trialrig run <trial file> --agent codex --out results/<name>/<arm>`.
