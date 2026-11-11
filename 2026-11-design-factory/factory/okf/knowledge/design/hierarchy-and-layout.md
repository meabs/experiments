---
type: Playbook
title: Visual hierarchy and layout
description: How to make one thing matter most on a screen - size, weight, space, alignment, grouping - and lay out mobile-first screens on a spacing scale.
tags: [design, layout]
status: draft
---

# Visual hierarchy and layout

## One screen, one order

Decide the order before drawing: 1 the thing the person came for (a balance, a question, a result), 2 what they need
to decide or do, 3 supporting detail, 4 everything else. Then make the look match the order.

| Tool | Use |
| --- | --- |
| Size | The first-rank item is clearly bigger: a jump of at least 1.4 times, not 1 px. |
| Weight | Two weights. Bold for what to read first, regular for the rest. |
| Colour and contrast | Full-strength text for content; muted text (still 4.5:1) for supporting detail. Brand colour marks what can be acted on. |
| Space | More space around more important things. Space separates groups better than lines or boxes. |
| Position | First-rank near the top; the main action where the thumb rests (bottom) or directly after the last input. |

Lower the emphasis of lesser things rather than raising everything. If everything is bold, nothing is.

## Space

- Use only the scale (4, 8, 12, 16, 24, 32, 48). Inside a group: 4 to 12. Between groups: 24 to 32. Between sections:
  32 to 48.
- A label is nearer to its own field than to the field above (proximity shows what belongs together).
- Side margins of 16 to 24 px on a phone; the same on every screen.
- White space is not waste. A calm screen with one clear thing beats a full one.

## Alignment and grouping

- Left-align text. Centre only short, single items (a result heading, an empty state).
- One left edge for everything on a screen. Amounts in lists right-align so digits line up.
- Group with space first, then a surface colour, then a hairline. Not all three. Avoid boxes inside boxes.
- Lists: one row height rhythm, the primary text and the amount on the first line, secondary text muted below.

## Screen skeleton (mobile)

1. Header: back or close on the left, a short title or step indicator, optional help on the right.
2. Heading (`h1`): the question or the state, in the largest text size used for headings.
3. Content: one column.
4. Actions: primary at the bottom, full width; a quieter secondary below or beside it. Keep the primary visible
   without scrolling on short screens when the content is short; never cover content with a fixed bar that hides
   focused fields.

On wider screens keep the column (maximum about 30rem for forms, 40rem for reading), centred, on a quiet background.
Do not stretch a phone layout across a desktop.

## Common faults to remove

Two primary buttons. Three or more text sizes within 2 px of each other. Borders and shadows together. Centred
paragraphs. Uneven gaps between like things. A heading that repeats the title bar. Icons with no label. Cards used
for single lines of text. Decoration bigger than the content.
