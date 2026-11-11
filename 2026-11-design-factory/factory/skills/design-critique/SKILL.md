---
name: design-critique
description: Stage 6. Review the built prototype as a senior designer would - first impression, hierarchy, consistency, journey, content, accessibility, industry and legal points - then fix the worst problems and record what was and was not checked.
---

# Design critique

**Read first:** `okf/rules/quality-bar.md`, the brief's success measures, the storyboard's screen list.
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

## Output shape

```
# Review: <name>
How it was reviewed: <seen in a browser / read from code>
## Per-screen notes
## Problems found (ranked) and what was done
## Checks (run / passed / failed / not run)
## Still open
```

Never write that the design is compliant or accessible. Write what was checked.
