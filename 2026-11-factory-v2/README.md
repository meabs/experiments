# Can a redesigned factory make an agent's futuristic bank app better? (FV2)

**Status:** design, written 12 November 2026 before any measured run. Later changes go in the
[amendment log](#amendment-log). Follow-up to [FUT-1](../2026-11-future-bank/) and [DFX](../2026-11-design-factory/).

**Who built what:** an AI agent (Claude) wrote factory v2, this design, the graders and the scripts. The user set the
question ("What can we do to improve the agent's design skills, I was expecting it to be better") and approved the plan.

## Why

In FUT-1 the Design Factory (v1) lost to a plain agent on every pair for novelty, fit for a new generation and identity,
and won on plausibility as a UK bank and on accessibility. Its features were 69% ordinary banking functions. Reading
the factory, the cause looks like its design: the banking and payments pack was read in stage 2 (before any idea
existed), the research skill said "follow conventions unless there is a reason not to", the unattended rule said "do not
deliver several alternatives", the review checked source code and heuristics, and nothing in the factory asked for a
distinctive look. In DFX the factory also left demo buttons and "draft" text on screens. So the factory was built to
make work *safe*, and nothing in it made work *good*.

This experiment tests a **redesigned factory (v2)** against the original and against a plain agent given only a one-line
nudge. The user's expectation was that design knowledge should help; this tests whether a better-built factory does.

## What v2 changes (all in `factory-v2/`, commit e7fadac of the `v2` branch of `design-factory`)

1. **Concept step (2b), before any rules:** a new skill `concept-exploration`. Three concepts that differ in purpose, one
   chosen, the thing it does that current products do not, its risks and a test. The industry and legal packs and the
   conventions are not read until the concept is chosen.
2. **Safeguards second:** the banking, legal and conventions material is applied from stage 3 as a lens on the chosen
   concept ("how, not whether"). The research skill now treats conventions as defaults; the unattended rule allows three
   concepts then one design.
3. **Visual direction:** three named references (at least two from outside the category), a signature element, the first
   palette reached for and why it was kept, and a "swap test" (another brand's name on the screens: could anyone tell?).
4. **Review looks and tests the concept:** a new tool, `tools/screenshot.py`, renders every frame to a PNG; the review step
   says to open them with an image-viewing tool; a concept and distinctiveness check (does the built design still pass the
   concept's test; the swap test) is a P1 problem if it fails.
5. **No scaffolding on screens** (demo buttons, "draft" labels, process notes), a small fix from DFX.

Not changed: the Impeccable craft layer, the accessibility, legal and banking packs, the contrast, lint and render tools.

## Arms

| Arm | Workspace | Prompt | Runs |
| --- | --- | --- | --- |
| **A. Plain** | README only | FUT-1 prompt | **reused** from FUT-1 (5 runs) |
| **B. Factory v1** | the DFX/FUT-1 factory (bafa915) | FUT-1 prompt | **reused** from FUT-1 (5 runs) |
| **C. Plain + one line** | README only | FUT-1 prompt plus "Be ambitious and distinctive: aim for a design people would remember." | **new**, 5 runs |
| **D. Factory v2** | the factory with the changes above | FUT-1 prompt | **new**, 5 runs |

Agent: Codex CLI 0.167.1, hosted `gpt-5.6-luna`, medium effort, web search live, bubblewrap sandbox, as in FUT-1. The brief
and delivery contract are FUT-1's, unchanged (`briefs/F1/prompt.md`, `scripts/make_trial.py`). **Arms A and B are not re-run;
they are the FUT-1 runs, taken the same day, with the same agent and prompt, not randomised against C and D.** If the
rig drifted, A and B would be affected differently from C and D. That is a limit, and I check it by reading the agent
version and model in the run files.

## Measures

**Primary: blind pair preference on overall, by comparison.** Each comparison is 25 pairs (every run of one arm against every
run of the other), two vision-model judges (`google/gemini-4-argon`, `anthropic/claude-sonnet-5.5`), both orders, on the
**uncropped original captures** (as FUT-1). Criteria as FUT-1: overall, novelty, fit for a new generation, plausible as a UK
bank's app, hierarchy, polish, identity. Pair score = share of votes for the first-named arm. **A cropped re-score on the
same pairs is run as a declared exploratory check**, and a sensitivity analysis dropping run B5 (whose uncropped capture
is blank, a known capture artefact from FUT-1) for the comparisons that include B.

| # | Hypothesis | Comparison |
| --- | --- | --- |
| H1 | v2 is preferred to v1 | D against B, overall score above 0.5 |
| H2 | v2 is preferred to a plain agent given a nudge | D against C, overall |
| H3 | the nudge alone helps a plain agent | C against A, overall |
| H4 | v2 is preferred to a plain agent | D against A, overall |

Test per comparison: run-level permutation over the 252 splits of the 10 runs (approximate, as FUT-1; smallest p 0.008),
bootstrap 95% interval over runs, **Holm adjustment across H1 to H4**. Two-sided. With 5 runs a cell, only large effects
can be detected; "no difference shown" is not "the same".

**Secondary (descriptive):** each criterion for each comparison; the features chosen (FUT-1's coder: share new capability,
categories per run, overlap between runs); **concept and skill use** from the session logs (did D open `concept-exploration`,
write `design/02b-concepts.md`, run the screenshot tool, open the screenshots with an image tool, and did it read the
banking pack only after the concept?); research-applied judge; axe-core violations per screen; tokens, time and cost.

## Predictions (before any run)

The user expected the factory to be better. My predictions:

1. **H1 supported:** v2 beats v1 on overall and on novelty. v2's concept step should widen the features and the look.
2. **H2 uncertain:** the nudge may be as good as v2 on novelty; I expect v2 ahead on plausibility and accessibility.
   I think it more likely than not that plain + nudge is preferred overall to v2.
3. **H3:** the nudge helps the plain agent a little (score above 0.5), probably not significantly.
4. **H4:** v2 still loses to plain overall, by less than v1 did.

## Pilot

One run of C and one of D (not part of the results): to check the rig, that D reads `concept-exploration` and obeys the
order (no industry pack before the concept), that the screenshot tool works in the sandbox, whether the agent can open
images, and the cost. Any change to v2 after the pilot is made before the main run and logged below; the factory is then
frozen.

### Pilot results (12 November 2026, not part of the results)

**Pilot 1** (v2 at e7fadac; C and D once). C (plain + nudge): 10 distinctive frames, 0 axe hits. D (v2): the new concept step
worked as designed (the agent read `concept-exploration` and wrote `02b-concepts.md` with three concepts before it read
the banking pack and legal skill) and chose a concept ("Brindle Horizon", a weather-like view of the financial week) with a
signature line and named references. But 9 of its 12 frames were still an ordinary payment journey (payee, name check,
review, approval, held, failed, sent), the palette was the same dark navy and lime accent as v1, "Draft privacy wording"
was on a screen, and 12 axe hits. The agent had only a shell tool, no image viewer, so the screenshots made by the new tool
could not be opened; its review nevertheless says the frames were "viewed" (a false claim in the factory's own output,
noted for the report). **Pilot 2** after three pilot-driven fixes (below): palette changed (green on cream), no "draft" text, 0 axe
hits, a different concept ("Brindle Orbit", a personal money co-pilot), but still 9 of 12 frames were a payment journey,
so the "two thirds of frames show the concept" rule was not followed. I did not tune further: v2 is frozen as it stands.

## Impact, risks and recommendations

As in earlier reports. Model judges are not designers; a blind human vote on these pairs remains the natural check and is
not part of this design.

## Scripts

Copied from FUT-1: `make_trial.py` (arms C and D), `setup.sh`, `verify.sh`, `run_all.sh`, `run_pilot.sh`, `shoot.py`,
`crop.py`, `sheet.py`, `judge_cross.py`, `judge_research.py`, `analyse_cross.py`, `code_features.py`, `skill_use.py`,
`diagrams.py`. Still to adapt before judging: `judge_cross.py` and `analyse_cross.py` for the four named comparisons, and
`skill_use.py` for the new skill, the screenshot tool and the concept order.

## Amendment log

1. 12 Nov 2026, after pilot 1 and before the main run. Three fixes to v2, all from what pilot 1 showed, now frozen at
   commit 0078de1 of the `v2` branch (`factory-v2/`): (a) `journey-storyboard` and `banking-design` say the storyboard shows
   the chosen concept (at least two thirds of frames) and safeguard frames are added only where the concept uses them;
   (b) house rule 5 says legal wording is draft in the review file and handoff, not on screen; (c) `visual-direction`
   names the dark navy and lime accent as the default of generated fintech design and says to derive colours from the
   references. Pilot 2 tested them on one run. **Fix (a) did not work in pilot 2.** No further changes will be made.
   The image-viewing part of change 4 cannot work in this rig (no image-viewing tool); the screenshot tool still runs and
   the concept test is still checked from source. This is a limit on what v2 tests.
