# Does a design factory give a better design than an agent that just builds?

**Status:** design, written 11 November 2026 before any measured run. Later changes go in the
[amendment log](#amendment-log).

**Who built what:** an AI agent (Claude) wrote the Design Factory, the briefs, the checklist, the graders and this
design, at the user's request. The user set the question, chose the two arms and gave the prediction.

## Why

A design and front-end team wants a "design factory": a fixed workflow an AI agent follows to take a brief through
research, a storyboard, a visual direction, a prototype and a review, using written skills (procedures) and an Open
Knowledge Format (OKF) bundle of design, accessibility, legal and industry knowledge. The alternative is to hand the
brief to the same agent and let it build.

The question (user, 11 November 2026): "I want to see an experiment of this vs a plain agent on a example banking
app", and "it's more about design looking vs just build". So the main measure is how the finished design looks and
reads to a reviewer, not whether process documents exist.

## Terms

- **Design Factory:** the folder in [`factory/`](factory/) (a snapshot of the `design-factory` repository at commit
  `8140e73`). `AGENTS.md` points to `okf/index.md`, the index that lists the workflow, 11 skills, three rules files
  and the knowledge files. About 17,000 words in all; an agent reads the parts the index says are relevant.
- **Skill:** a written procedure for one kind of work (for example `journey-storyboard`), in `skills/<name>/SKILL.md`.
- **OKF (Open Knowledge Format):** a folder of short markdown files with an index, as used in earlier experiments here.
- **Storyboard:** the journey written as numbered frames (what the customer wants, sees and does, and what the system
  does back), including failures, before anything is built.
- **Prototype:** a clickable front end in plain HTML, CSS and JavaScript that runs offline.
- **axe-core:** an open-source accessibility checker that tests a page against WCAG rules. It finds only the failures
  a program can detect.
- **WCAG 2.2 AA:** the Web Content Accessibility Guidelines, version 2.2, level AA: the usual accessibility target.

## Arms

Two arms, as the user asked ("Two arms only"; "Don't do lots of arms"). Same agent, model, prompt and settings; they
differ only in the files in the workspace.

| Arm | Workspace contains |
| --- | --- |
| **A. Plain agent** | a README saying this is Brindle Bank's design workspace. Nothing else. |
| **B. Design Factory** | the same, plus the factory: `AGENTS.md`, `CLAUDE.md`, `okf/`, `skills/`, `tools/` |

Agent: Codex CLI 0.167.1 with hosted `gpt-5.6-luna`, medium reasoning effort, web search off, inside the bubblewrap
sandbox used in earlier experiments (the experiment folder, checklist and other runs are not visible to the agent).
Codex loads `AGENTS.md` by itself, so the prompt does not mention the factory.

## Briefs

Six briefs for the mobile app of Brindle Bank, a fictional UK retail bank (a web search on 11 November 2026 found no
bank of that name). Each is a short ticket with example data, in [`briefs/`](briefs/). No brief restates a rule,
names a state to design or asks for research or a storyboard.

| Brief | Journey | Kind |
| --- | --- | --- |
| D1 | pay someone new | regulated journey (payments) |
| D2 | open a savings account | regulated journey (savings) |
| D3 | ask for an arranged overdraft | regulated journey (credit) |
| D4 | my card is missing | service journey (cards) |
| D5 | where did my money go this month? | mostly visual (spending summary) |
| D6 | account home | mostly visual (home screen) |

The prompt is identical in both arms: one sentence of context, the brief, and a delivery contract
(`scripts/make_trial.py`): a prototype at `prototype/index.html` that runs offline, designed for a 390 px wide phone;
every screen and state also opens directly at `index.html#<screen-id>`; `prototype/screens.json` lists them in
journey order; nobody is available to answer questions. The contract exists so every screen can be opened and
photographed by a script.

**5 runs per brief per arm: 60 runs, 30 pairs.** Plain run *i* of a brief is paired with factory run *i* of the same
brief (run numbers are assigned by the rig before anything is produced).

## Measures

### Main: which design does a reviewer prefer? (blind, side by side)

`scripts/shoot.py` opens every screen in a headless browser at 390 by 844 and takes a screenshot.
`scripts/sheet.py` tiles them three to a page, numbered, with no names or ids. For each pair, two vision models from
providers other than the agent's (`google/gemini-4-argon`, `anthropic/claude-sonnet-5.5`) are shown the brief and the
two designs as "Design 1" and "Design 2" and asked which is better on each criterion, or a tie
(`scripts/judge_pairs.py`):

| Criterion | What the judge is asked |
| --- | --- |
| hierarchy | on each screen it is obvious what matters most and what to do next |
| polish | consistent components, spacing, alignment and typography; looks finished |
| identity | a deliberate, distinctive look that suits a bank, not generic defaults |
| content | clear, specific, helpful words |
| trust | would a customer trust this with their money |
| journey | the right steps in order, and the situations a real customer could hit are designed (whole-design view only) |
| **overall** | which design should the bank's design lead take forward |

Two views, judged separately:

- **Whole design:** every screen of each design (up to 18).
- **Looks only:** the first six screens of each design, so both arms show the same amount of material and a design
  can't win by having more screens.

Each judge sees each pair in both orders (which design is "Design 1" is swapped), because the pilot showed a strong
position effect (below). So each pair-view has four votes. **Pair score** = share of votes for the factory's design
(a tie counts half): above 0.5 the factory wins the pair, below 0.5 the plain agent wins, 0.5 is a split. A run that
delivers no screens loses its pair.

The judges never see file names, screen ids, the arm, the process files or the agent's messages.

**People's votes (exploratory):** `scripts/gallery.py` will build a page showing each pair blind, in random order
and sides, for the user and their design team to vote on. If votes are collected they are reported next to the
models' votes, as a separate table. Model judges are a stand-in for designers' judgement, not a replacement; the
report will say how far they agree.

### Secondary

1. **Checklist** ([`key/states.json`](key/states.json), written before any run's output was read): 12 items per
   brief that a complete design of that journey has, none stated in the brief. Two kinds: *state* (a screen or state,
   such as the name-check result or a declined screen) and *info* (information the screens should carry, such as the
   summary box, with the rule it comes from). `scripts/judge_states.py` gives a text model the visible text of every
   screen and asks, per item, present or not with an exact quote; a "present" whose quote is not on a screen is
   rejected by the script. I check every rejected quote by hand and a random fifth of the other decisions (seed 1);
   corrections go in `states-overrides.json`. Score: share of the 12 items present.
2. **Accessibility, measured by program** (`scripts/shoot.py`, no model): axe-core 4.10.3 violations of WCAG 2.0, 2.1
   and 2.2 A and AA rules per screen (primary accessibility number); share of screens with none; screens that scroll
   sideways at 320 px; share of controls at least 24 px and 44 px in both directions; clickable things that can't be
   reached by keyboard; one `h1` per screen. These catch only what a program can detect; no claim of conformance is
   made for either arm.
3. **Cost:** input, cached and output tokens, seconds, and cost at list price per run.
4. **Process and honesty (descriptive):** which design files each run wrote; whether the factory's stages were
   followed; whether the final message claims accessibility or compliance; for D2, which FSCS limit the prototype
   shows (£120,000 since 1 December 2025; £85,000 before).

## Hypotheses and the user's prediction

**The user's prediction (11 November 2026):** "Little difference" (the option read: "A capable plain agent already
does most of this; the factory mainly costs more tokens").

| | Hypothesis | Test |
| --- | --- | --- |
| H1 | Whole design: the factory's design is preferred (mean pair score differs from 0.5) | two-sided sign-flip permutation test on pair scores minus 0.5 |
| H2 | Looks only: the factory's design is preferred | same |
| H3 | The factory's prototypes contain more of the checklist | sign-flip test on per-pair differences (factory minus plain) |
| H4 | The factory's prototypes have fewer axe violations per screen | same |
| H5 | The factory costs more tokens and time | descriptive: ratio with the two means |

All tests are two-sided, so a result against the factory is detected as readily as one for it. 30 pairs; exact
enumeration where possible, otherwise 10,000 resamples, seed 1; bootstrap 95% intervals (10,000, seed 1); Holm
adjustment across H1 to H4. An exact sign test on pair wins is reported beside H1 and H2. Results are also shown per
brief and per criterion, without tests. A non-significant result will be reported as "no difference shown", not as
"the same".

With 30 pairs the sign test can detect a preference of roughly 75% or more of pairs; a smaller true preference could
be missed.

## Pilot (11 November 2026, not part of the results)

Plain arm once on each brief; factory once on D1 and D5 (`results/pilot/`). Purpose: prove the rig, check the plain
agent isn't already at the top of every measure, and measure cost.

- All 8 runs met the delivery contract. Plain: 2 to 10 screens, about 94k tokens and 131 s a run. Factory: 8 and 13
  screens, all six stage files written, about 583k tokens and 338 s a run (about 6 times the tokens, 3 times the cost
  at list price because most input is cached: $0.013 against $0.041).
- No ceiling: plain prototypes had 3 to 8 of 12 checklist items; 5 of 6 had colour-contrast violations.
- The judges are sensitive to order: one judge chose the design shown first in 7 of 8 calls. Hence both orders for
  every pair and the pair score above.
- With two pairs nothing can be concluded about preference; the numbers are in `results/pilot/analysis.md`.

Changes made after the pilot, before any measured run: checklist item D2-05 replaced (it depended on D2-04); the
quote check accepts a quote stitched from several elements if four consecutive words are on a screen; console errors
caused by the checker itself are no longer counted.

## Limits known in advance

- **One author.** The same AI agent wrote the factory, the briefs, the checklist and the graders, in that order of
  commit but in one sitting, with the briefs' topics already in mind. Every checklist item is covered by the factory's
  knowledge files (`in_factory` is true for all 72). So the checklist measures whether the factory gets its own
  knowledge into the prototype, not whether that knowledge is right or complete. The preference judgement and the
  axe checks do not share this weakness.
- **The factory's regulatory content is draft.** A few points were checked against regulators' pages by search
  summary on 11 November 2026; many are from the author's knowledge and marked "check current rule". The experiment
  does not test whether the designs are legally compliant, and neither arm's output should be treated as such.
- **Model judges, not designers.** Vision models judge screenshots. They may reward things designers wouldn't. The
  blind gallery lets people check.
- **Screenshots, not use.** Judges see still screens opened by address, not the journey being used. Behaviour
  (navigation, validation as you type) is only partly covered by the program checks.
- **One model, one agent, one industry, short briefs, no web access, nobody answering questions.** The factory is
  run unattended, which is not how a design team would mostly use it.
- **Two arms.** There is no arm with the same knowledge as a single plain file, or with a one-line instruction, so
  the experiment cannot say which part of the factory (workflow, skills, knowledge, tools) causes any difference.

## Cost

`gpt-5.6-luna` list price (5 November 2026): $0.20 per million input tokens, $0.02 cached, $1.20 output. From the
pilot, the 60 runs should cost about $2 and take under an hour; judging about $5.

## Reproduce

```bash
python3 -I scripts/make_trial.py                       # trial files
bash scripts/run_all.sh                                # 60 runs -> results/main
~/code/benchmark/webmcp-exp/env-plain/bin/python scripts/shoot.py results/main
python3 scripts/sheet.py results/main
uv run --with requests --with pillow python scripts/judge_pairs.py results/main
uv run --with requests --with pillow python scripts/judge_pairs.py results/main --judge anthropic/claude-sonnet-5.5
uv run --with requests python scripts/judge_states.py results/main
python3 -I scripts/analyse.py results/main
```

## Amendment log

None yet.
