---
type: Playbook
title: Typography and colour
description: Type scale, weights and line length; colour roles, contrast pairs and status colours, written as tokens.
tags: [design, typography, colour]
status: draft
---

# Typography and colour

## Type

- **Family.** A system stack keeps prototypes offline and fast:
  `system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`. A serif from the system
  (`Georgia, "Times New Roman", serif`) for large headings or amounts is a legitimate way to give character.
- **Scale.** 5 or 6 steps with visible jumps, in rem. Example: 0.8125 (13 px, captions only), 0.9375 (15, secondary),
  1.0625 (17, body), 1.375 (22, headings), 1.75 (28, screen headings), 2.5 (40, the hero number). Body text is never
  under 16 px on a phone; nothing is under 13 px.
- **Weights.** 400 and 600 or 700. Use weight for hierarchy before reaching for colour.
- **Line height.** About 1.5 for body, 1.2 to 1.3 for large headings. Line length 45 to 75 characters.
- **Numbers.** `font-variant-numeric: tabular-nums` wherever figures are compared or change. Pence may be set smaller
  than pounds in a hero amount, but must stay readable.
- Sentence case. No all-caps for anything longer than two words. No justified text. Underline links in body text.

## Colour roles

Name what a colour is for:

| Token | For |
| --- | --- |
| `--bg` | the page |
| `--surface` | cards, sheets, fields |
| `--text` | main text (aim for 12:1 or more on `--bg`) |
| `--text-muted` | secondary text (at least 4.5:1 on both `--bg` and `--surface`) |
| `--primary`, `--on-primary` | the main action and text on it (at least 4.5:1) |
| `--border` | field and control edges (at least 3:1 against what is behind them) |
| `--focus` | the focus ring (at least 3:1 against adjacent colours) |
| `--danger`, `--warning`, `--success`, `--info` plus a tinted background and a text colour for each | status |

Rules:

- One brand hue. Build neutrals with a little of that hue in them rather than pure grey; it makes the whole thing
  feel designed.
- Off-white backgrounds and near-black text are easier to read than pure white and pure black.
- Status colours are for status only. Red means danger or an error, never "sale" or decoration. Warning (amber) text
  needs a dark amber or dark text on a tinted background to pass contrast; yellow on white fails.
- Never rely on colour alone: pair it with an icon and words ("Declined", "Pending").
- Check every pair with `python3 tools/contrast.py <foreground> <background>`. Normal text 4.5:1; large text (24 px,
  or 18.66 px bold) 3:1; control edges, icons that carry meaning and focus rings 3:1.
- Disabled controls are exempt from contrast rules but prefer leaving buttons enabled and explaining on press.
- If you offer a dark theme, give every token a dark value; do not invert.

## Shape and depth

One radius for controls (for example 12 px), one for containers (16 to 20 px). One soft shadow for things that float
above the page (sheets, bars); otherwise separate with surface colour. Hairlines at 1 px in `--border` or a lighter
divider token that is decorative only.
