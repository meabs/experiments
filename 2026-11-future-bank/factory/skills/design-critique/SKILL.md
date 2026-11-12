---
name: design-critique
description: Stage 6. Review the built prototype as a senior designer would - first impression, hierarchy, consistency, journey, content, accessibility, industry and legal points - then fix the worst problems and record what was and was not checked.
---

# Design critique

**Read first:** `okf/rules/quality-bar.md`, the brief's success measures, the storyboard's screen list.
Use `skills/impeccable/SKILL.md` for this stage: score the ten heuristics and the cognitive-load checklist and walk the journey as personas (`reference/critique-reference.md`), run `reference/audit.md`, then fix with `polish.md`, `harden.md`, `adapt.md` and `distill.md`.
**Writes:** `design/05-review.md`; changes to the prototype; then `frontend-handoff`.

## Steps

1. **Look at it.** If a browser or screenshot tool is available, open every screen at 390 px and 320 px wide and look.
   If not, read each screen's HTML and CSS top to bottom and picture it; say in the review that it was read, not
   seen.
2. **Five-second test per screen.** What is this screen for? What is the main action? What is the most prominent
   thing, and should it be? Write one line per screen.
3. **Squint test.** Is there one clear order of importance? More than one filled button? Competing colours? Uneven
   gaps? Text sizes that are nearly but not quite the same?
4. **Consistency sweep.** Same component, same look, same words for the same thing on every screen. Search the CSS
   for values not taken from tokens.
5. **Walk the journey** as the hardest-case user from the brief: main path, then each branch and failure. Note where
   they would hesitate, lose their place or be unsure what happened.
6. **Specialist passes.** Run `accessibility-review`, `content-design` step 6 (read aloud), the industry checklist
   and `legal-review`'s register.
7. **Rank and fix.** List problems with a severity (blocks the task, causes mistakes or worry, looks unfinished,
   polish). Fix every one in the first two groups and as many of the third as time allows. Re-run the lint tool.
8. **Record.** In the review file: what was fixed, what remains and why, and a table of checks marked run, passed,
   failed or not run.

## Required outputs (the stage is not done without them)

Write each into `design/05-review.md`, or the review file the brief names. If a check cannot be run, write "not run" and
the reason; do not leave it out.

1. **Design review with Impeccable** (`skills/impeccable/reference/critique-reference.md`):
   - per screen: the five-second test and the squint test, one line each;
   - the ten usability heuristics, each scored 0 to 4 with one line of evidence (a table, total out of 40);
   - the cognitive-load checklist, with the failures named;
   - the journey walked as at least three personas (always the accessibility-dependent user and the distracted mobile
     user; for money journeys add the confused first-timer), with the red flags found;
   - a ranked problem list (P0 to P3), then `reference/audit.md` for the technical pass.
2. **Accessibility review:** the table from the accessibility-review skill. Evidence: `python3 tools/lint_prototype.py
   <folder>` and `python3 tools/render_check.py <folder>` (rendered contrast, target sizes, names; it cannot check
   320 px reflow, so say that is read from the CSS), plus source reading for keyboard and focus.
3. **Legal review:** the register from the legal-review skill, or one line saying why it does not apply.
4. **Industry checklist:** the banking-design checklist, nine answers, for banking briefs.
5. **Research trace:** a table: each research decision (R1, R2, ...), applied or not, and where it can be seen.
6. **Fixes:** fix every P0 and P1 problem and every failed check you can fix, re-run the lint and render checks, then
   record what was fixed and what remains.

## Output shape

```
# Review: <name>
How it was reviewed: <seen in a browser / read from code>
## Design review (Impeccable): per-screen, heuristics table, cognitive load, personas
## Accessibility review
## Legal register
## Industry checklist
## Research trace
## Problems found (ranked) and what was done
## Checks (run / passed / failed / not run)
## Still open
```

Never write that the design is compliant or accessible. Write what was checked.
