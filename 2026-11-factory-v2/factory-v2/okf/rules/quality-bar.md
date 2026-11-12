---
type: Rule
title: Quality bar
description: What good means for a screen and a journey, and the checks a prototype must pass before it is called finished.
tags: [rules, quality]
status: draft
---

# Quality bar

## A screen is good when

- **One job.** A stranger can say what the screen is for and what to do next within five seconds.
- **One primary action.** At most one filled, high-emphasis button. Everything else is quieter.
- **Clear order.** Size, weight and space show what matters most, second and third. Squint: the right thing stands
  out.
- **Consistent.** The same thing looks and behaves the same everywhere. All values come from the tokens.
- **Aligned and spaced on a scale.** Edges line up. Related things are close; unrelated things are apart. No
  accidental spacing.
- **Real content.** Realistic names, amounts and dates, including long ones. Nothing overflows or truncates the part
  that matters.
- **Honest.** Nothing is hidden, rushed or made to look more certain than it is.

## A journey is good when

- The person always knows where they are, what has happened and what happens next.
- Anything that moves money, shares data or cannot be undone has a review step that repeats the key facts, and a
  clear result afterwards.
- Every failure has a screen that says what happened, in plain words, whether anything was taken or changed, and what
  to do now.
- Going back never loses what was typed. Nothing happens twice if a button is pressed twice.
- There is a way to get help from a person on any screen where someone could be stuck or worried.

## It has a look, on purpose

The direction can be described in one sentence that someone could disagree with (for example "calm and editorial:
large numerals, lots of white, one deep green"). Default system-blue buttons on grey cards with no decision behind
them is not a direction.

## Before a prototype is called finished

| Check | How |
| --- | --- |
| Every storyboard screen and state exists and is reachable | walk the storyboard list against the prototype |
| Lint passes | `python3 tools/lint_prototype.py <folder>` |
| Text contrast at least 4.5:1 (3:1 for large text and for the edges of controls) | `tools/contrast.py` on every token pair used |
| Works at 320 px wide with no sideways scrolling; text can be enlarged to 200% | check the CSS: no fixed widths, relative units |
| Everything works with a keyboard, focus is always visible, order follows the screen | read the HTML order; native elements |
| Touch targets at least 44 by 44 px (never under 24) | check control sizes in the CSS |
| Every field has a visible label; errors say what is wrong and how to fix it, next to the field | read each form |
| No placeholder text, no dead buttons, no console errors | read through; run if a browser is available |
| Industry and legal checklists done, open points listed | the relevant skills |

List anything not checked as "not run" in the review file.
