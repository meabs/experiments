---
name: journey-storyboard
description: Stage 3. Storyboard the journey as numbered frames - main path, branches, failures and recovery - and produce the complete list of screens and states to build.
---

# Journey storyboard

**Read first:** `design/01-brief.md`, `design/02-research.md`, `okf/knowledge/design/components-and-states.md`.
Also read `skills/impeccable/reference/shape.md` to plan the UX before drawing frames.
**Writes:** `design/03-storyboard.md`.

A storyboard here is a sequence of frames. Each frame is one moment: what the person wants, what they see, what they
do, and what the system does back. It is written before any visual decisions.

## Steps

1. **Main path.** 4 to 8 frames from the entry point to a clear end. End on what the person sees after it is done,
   not on the button press.
2. **Branches.** For each decision or system answer in the main path, add the other outcomes found in research
   (declined, warning, not available, needs more information).
3. **Failure and recovery.** Validation errors, no connection, time-out, pressing twice, going back, giving up
   half-way. For each: what the person is told, what state their money or data is in, what they can do now.
4. **Frame format.** Use this for every frame:

   ```
   ### F3 Review payment            (screen id: review)
   Wants: to be sure it is the right person and amount before it goes
   Sees: payee name as checked, sort code and account number, amount large, when it will arrive, fee (none)
   Does: confirms, or goes back to change
   System: asks for approval -> F4; if connection lost -> F4c
   Feels: careful -> reassured
   ```
5. **Screen and state list.** A table of every screen id with its states (default, loading, empty, error, success,
   disabled, long content). This list is the contract for stage 5: everything in it gets built.
6. **Check the story.** Read the frames in order as the hardest-case user from the brief. Where would they be lost,
   worried or stuck? Fix the frames.

## Good storyboards

- Give every screen a short stable id in lowercase with hyphens. The prototype uses the same ids.
- Put information where the decision is made, not on a later screen.
- Show what happens next on every end screen ("arrives in minutes", "we'll email you within 2 working days").
- Keep the count honest: fewer, clearer screens beat many thin ones, but never drop a failure state to save a screen.

## Done when

Every outcome named in the research has a frame, and the screen and state list could be handed to someone else to
build.
