---
name: visual-direction
description: Stage 4. Choose one deliberate visual direction and write it as design tokens - type scale, colour roles with checked contrast, spacing, shape, elevation and the core components.
---

# Visual direction

**Read first:** `okf/knowledge/design/hierarchy-and-layout.md`, `okf/knowledge/design/type-and-colour.md`,
`okf/rules/quality-bar.md`; the industry file on tone and trust if one applies.
Then read `skills/impeccable/SKILL.md` (its precedence section first), `reference/operate.md` and the "Refuse" list in `reference/craft-floor.md`; use `reference/typeset.md`, `colorize.md` and `layout.md` for those choices. The direction must be specific to this product, not the category's defaults.
**Writes:** `design/04-direction.md` (about 250 words plus the token block).

## Steps

1. **Three words and a sentence.** Pick three words for how it should feel to the user in this journey (for example
   "calm, exact, human") and one sentence describing the look that someone could disagree with. Say what you are
   deliberately not doing.
2. **Type.** One typeface family from the system stack (no downloads). A scale of 5 or 6 sizes with a clear jump
   between steps (for example 13, 15, 17, 22, 28, 40 px, written in rem). Two weights, three at most. Decide where
   the largest size is used (usually the one number or heading that matters). Numbers that people compare use
   tabular figures.
3. **Colour.** Name roles, not colours: `--bg`, `--surface`, `--text`, `--text-muted`, `--primary`,
   `--on-primary`, `--border`, `--danger`, `--warning`, `--success`, `--focus`. One brand colour and one accent at
   most. Run `python3 tools/contrast.py` on every text and background pair you will use and write the ratios in the
   file. Fix failures now, not later.
4. **Space and shape.** A spacing scale (4, 8, 12, 16, 24, 32, 48). One corner radius for controls and one for
   containers. One shadow level or none. Screen side margins.
5. **Core components.** Describe in a line each: primary button, secondary button, text link, text field with label,
   hint and error, list row, card, banner (information, warning, error, success), bottom action bar, header. State
   heights (controls at least 48 px) and how focus looks (a 3 px outline with an offset, visible on every surface).
6. **One hero moment.** Decide the one place in the journey where the design does something memorable and useful
   (the amount on the review screen, the confirmation, an empty state). Everything else stays quiet.
7. **Write the tokens** as a CSS `:root { ... }` block, ready to paste into the prototype.

## Avoid

- Picking defaults and calling it a direction. Grey cards and a blue button need a reason like anything else.
- More than one filled button colour, more than three text colours, shadows and borders on the same element,
  centred body text, all-caps labels, text under 14 px, pure black on pure white for long text.
- Colour as the only signal. Status always has words or an icon with a text name as well.
- Decoration that competes with the main thing on the screen.

## Done when

Another person could build any screen from the tokens and component lines without asking what something should look
like, and every text pair has a passing contrast ratio written next to it.
