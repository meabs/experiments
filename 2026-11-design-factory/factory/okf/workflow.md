---
type: Process
title: Design Factory workflow
description: The six stages from brief to handoff, the file each stage writes and the check that ends it.
tags: [workflow]
status: draft
---

# Workflow

Six stages, in order. Each stage has one skill, writes one file (or folder), and ends with a short check. Do not skip
a stage and do not merge stages into one file: the point of the factory is that the look and the journey are decided
on purpose before anything is built.

Keep the early stages short. Stages 1 to 4 together should take well under half of the effort; they exist to make the
build better, not to produce long documents.

| # | Stage | Skill | Writes (default path) | Stage is done when |
| --- | --- | --- | --- | --- |
| 1 | Brief | brief-intake | `design/01-brief.md` | users, goal, constraints, assumptions and 3 to 5 success measures are written; open questions are listed |
| 2 | Research | design-research | `design/02-research.md` | every finding names its source type; each finding ends in "so the design should..."; risks are listed |
| 3 | Storyboard | journey-storyboard (+ impeccable shape) | `design/03-storyboard.md` | main path, each branch and each failure has frames; the screen and state list is complete |
| 4 | Visual direction | visual-direction (+ impeccable) | `design/04-direction.md` | tokens are chosen and contrast-checked; the direction is stated in one sentence a person could disagree with |
| 5 | Prototype | prototype-build (+ impeccable craft floor) | `prototype/` | every screen and state in the storyboard exists and can be reached; the lint tool passes |
| 6 | Critique and handoff | design-critique (+ impeccable), frontend-handoff | `design/05-review.md`, `design/06-handoff.md` | every required review output below exists, the top problems are fixed in the prototype, and checks not run are listed as not run |

If the brief names output files or folders, use those instead of the defaults, and keep any extra stage files next to
them.

## The review is mandatory

Stage 6 is not done until `design/05-review.md` contains all of these (see the design-critique skill for how):

1. **Design review with Impeccable:** per-screen five-second and squint tests; the ten usability heuristics scored 0 to
   4; the cognitive-load checklist; a walk of the journey as at least three personas; a ranked list of problems.
2. **Accessibility review:** the checklist table, with evidence (lint, render check, source reading) or "not run".
3. **Legal review:** the register, where legal-review applies, or a line saying why it does not.
4. **Industry checklist:** for banking, the nine questions in the banking-design skill.
5. **Research trace:** each research decision, and whether the built design applies it.
6. **Fixes:** what was fixed and what remains.

## Research feeds the design

Stage 2 ends with a numbered list of **decisions** (R1, R2, ...), each saying what the design will do and why. Stage 3
frames and stage 4 tokens name the decisions they apply. Stage 6 checks that every decision is visible in the built
design and says so, or says which were dropped and why. A decision that cannot be seen in a frame is not a decision.

## Which specialist skills run where

| Specialist skill | Stage 2 | Stage 3 | Stage 4 | Stage 5 | Stage 6 |
| --- | --- | --- | --- | --- | --- |
| content-design | | frame captions and key messages | | all screen text | read every screen aloud |
| accessibility-review | | focus order, error and timeout branches | contrast of every token pair | semantics, keyboard, target size, reflow | full checklist |
| legal-review | what applies to this journey | where notices, consent and prices appear | | exact placement and wording status | register of open points |
| impeccable (craft layer) | | shape | direction: refuse the defaults | craft floor | heuristics, audit, polish |
| industry skill (for example banking-design) | conventions, risks, regulated information | industry-specific branches | trust and tone | industry components | industry checklist |

## Order of reading for a new brief

1. `okf/index.md`, this file, and the three rules files.
2. The stage 1 skill. Decide which industry applies and whether personal data, consent, prices or claims are involved.
3. For each later stage: its skill, then only the knowledge files that skill names for this brief.

## Changing direction

If stage 5 or 6 shows the storyboard or direction was wrong, change the earlier file first, then the prototype, and
note the change at the bottom of the earlier file under "Changes". The files must describe what was built.
