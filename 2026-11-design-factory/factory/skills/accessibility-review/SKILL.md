---
name: accessibility-review
description: Design for and check a prototype against WCAG 2.2 level AA - structure, names, keyboard, focus, contrast, target size, reflow, forms, errors, status messages, time limits - recording what was checked and how.
---

# Accessibility review

**Read first:** `okf/knowledge/accessibility/wcag-22-aa.md`,
`okf/knowledge/accessibility/keyboard-and-semantics.md`.

Use this skill twice: while designing (stages 3 to 5) so problems are not built in, and as a check in stage 6.

## While designing

- Storyboard: note focus order for each frame; include a time-out frame if the journey has a time limit; make sure no
  step depends on memory, a puzzle or on colour alone.
- Direction: run `tools/contrast.py` on every pair; design the focus indicator; make controls at least 48 px high.
- Build: native elements, one `h1` per screen, labels, landmarks, logical source order.

## Check (stage 6)

Go through the checklist file in order for every screen and state. For each line record pass, fail (with the screen
id and what is wrong) or not run.

1. Automated: `python3 tools/lint_prototype.py <folder>`. If axe, Lighthouse or a browser is available, run them and
   keep the output. Zero automated findings does not mean accessible.
2. Keyboard, by reading the HTML if no browser: every action is a `button`, `a[href]` or form control; order matches
   the screen; nothing has a positive `tabindex`; dialogs keep focus inside and return it on close; focus moves to
   the new screen's heading on a screen change.
3. Names: every control has a visible text label that is also its accessible name; icon-only buttons have
   `aria-label`; decorative SVG has `aria-hidden="true"`.
4. Forms and errors: each field's hint and error are tied with `aria-describedby`; invalid fields have
   `aria-invalid="true"`; an error summary with `role="alert"` receives focus on submit; nothing is conveyed by
   colour or placeholder alone.
5. Status: results that appear without a screen change (saved, sending, name checked) are in an element with
   `role="status"` or `role="alert"`.
6. Sizing: no sideways scroll at 320 px; text in rem; no fixed heights around text; targets at least 44 by 44 px.
7. Motion and time: honour `prefers-reduced-motion`; warn before any time-out and let the person extend it.

## Report

A table in `design/05-review.md`: check, result, evidence. Fix failures in the prototype before finishing. Never
state that the prototype conforms to WCAG; state which checks were run and their results.
