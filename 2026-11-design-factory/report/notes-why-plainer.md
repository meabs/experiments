# Why the factory looked plainer (notes for REPORT.md; revised after checking the first explanation)

## What was checked (all 60 storyboards, measured from the HTML; plain vs factory means)
| Measure | Plain | Factory |
| --- | --- | --- |
| Status-bar clock (9:41) in the page (device-mockup chrome) | 77% of runs | 17% |
| Distinct hex colours in the file | 31 | 17 |
| CSS custom properties (design tokens) | 11 | 21 |
| Research tags (R1, R2...) visible on the frames, per run | 6.0 | 1.5 |
| "Show / Simulate ... error" demo buttons, per run | 0.0 | 0.5 |
| "Draft / placeholder / for review" wording, per run | 2.4 | 4.4 |
| Share of the first six frames that are state or failure frames | 11% | 23% |
| Screens delivered | 7.3 | 9.7 |

Judge reasons (looks view, 120 votes): of the 82 votes plain won, 45 praised a polished, finished, real-app look and
38 criticised the other design's prototype scaffolding or generic look; frame cropping was cited equally in votes
either arm won (19 vs 21), so it is not the cause.

## What the first explanation got wrong
- "The factory spends its first six frames on states": true but small (about 1.4 frames of 6 against 0.7).
- "Phone bezels": the first CSS check matched every file and was dropped; the status-bar clock is the usable proxy.
- "Rules ask for one brand colour so it is plainer": partly true (17 v 31 colours) but not the main cause.

## What the evidence supports
1. The two arms built different things from the same word "storyboard". Plain built an illustrated presentation:
   numbered steps, narrative captions, device mockups with a status bar, research tags on each frame, a bolder
   palette. The factory's journey-storyboard and prototype-build skills define the storyboard as a working prototype
   of every screen and state: one screen at a time, a centred column, tokens only, demo controls to reach error
   states, draft legal wording marked as draft. That is more complete and more accessible (H3, H4) but looks like a
   product under test, not a polished mockup.
2. The "looks" measure shows the first six frames as screenshots, so it partly rewards presentation chrome (device
   bezel, status bar, hero card) that is a property of the storyboard page, not of the screen design. This is a
   confound in H2 that the report must state. Checking it would need a re-judge with frames cropped to the screen
   interior (not done; offered as a follow-up).
3. H6 gap (68% v 81%) is consistent with plain tagging each frame with its research decisions (6.0 v 1.5 visible
   tags) while the factory keeps the trace in 05-review.md; the research judge reads the frames and research.md only.
   This is consistent with the data, not proven.

## Not established
- That any single skill caused the look; no ablation was run.
- That a person would prefer the plain storyboards; judges were models.

## Cropped re-score result (amendment 1)
Looks only: 0.32 original, 0.32 cropped (plain ahead in 19 of 30, p 0.009): cropping did not close the gap, so the
presentation-chrome confound hypothesis is NOT supported for looks. Whole design: 0.53 original, 0.38 cropped
(p 0.15, not significant), moving towards plain. Identity stays at 0.12 to 0.15; polish falls for the factory
(0.44 to 0.24 whole). Caveat: the crop and the wider viewport changed together; a status bar inside the glass is kept.
