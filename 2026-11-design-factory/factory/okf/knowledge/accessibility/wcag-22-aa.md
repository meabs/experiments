---
type: Checklist
title: WCAG 2.2 level AA checklist for prototypes
description: The WCAG 2.2 A and AA success criteria that design and front-end work most often fails, each with how to meet it in a prototype.
tags: [accessibility, wcag]
status: draft
sources:
  - title: Web Content Accessibility Guidelines (WCAG) 2.2, W3C Recommendation
    resource: https://www.w3.org/TR/WCAG22/
    checked: criterion numbers and thresholds written from the standard as known to the author; confirm wording against the standard for any formal finding
---

# WCAG 2.2 AA checklist

Not the whole standard: the parts that most often go wrong in app journeys. Numbers are success criteria.

## See

| Check | Criterion | How to meet it |
| --- | --- | --- |
| Text contrast 4.5:1; large text (24 px, or 18.66 px bold) 3:1 | 1.4.3 | check every token pair, including muted text, text on buttons, on tinted panels and placeholder text if any |
| Edges of fields and buttons, meaningful icons, focus rings 3:1 | 1.4.11 | a visible field border, not a faint hairline |
| Colour is never the only signal | 1.4.1 | add words or an icon with a name to status, errors, selected items, links in text |
| Reflow at 320 px wide, no sideways scroll | 1.4.10 | fluid widths, wrapping |
| Text resizes to 200% | 1.4.4 | rem units, no fixed heights around text, zoom not disabled |
| Text spacing can be increased | 1.4.12 | no clipping when line height and spacing grow |
| Works in portrait and landscape | 1.3.4 | do not lock orientation |
| Images and icons have text alternatives; decoration is hidden | 1.1.1 | `alt`, `aria-label`, or `aria-hidden="true"` |

## Structure and names

| Check | Criterion | How to meet it |
| --- | --- | --- |
| Headings, lists, tables, groups are real elements | 1.3.1 | one `h1` per screen, no skipped levels, `fieldset` and `legend`, `ul`, `dl` for label and value pairs |
| Reading order matches the screen | 1.3.2 | source order; no reordering with CSS that changes meaning |
| Page has a language and a title that changes per screen | 3.1.1, 2.4.2 | `lang="en-GB"`, set `document.title` on a screen change |
| Every control has a name and role | 4.1.2 | native elements; visible label text is in the accessible name (2.5.3) |
| Field purpose is identified | 1.3.5 | `autocomplete` on personal data fields |
| Link and button text makes sense alone | 2.4.4 | "Change amount", not "Change" five times (add visually hidden text) |

## Operate

| Check | Criterion | How to meet it |
| --- | --- | --- |
| Everything works by keyboard, no traps | 2.1.1, 2.1.2 | buttons and links, Escape closes sheets |
| Focus order is logical and focus is visible | 2.4.3, 2.4.7 | never `outline: none` without a replacement; use `:focus-visible` with a 3 px ring |
| Focused item is not hidden by sticky bars | 2.4.11 | `scroll-padding`, sticky not fixed overlays |
| Target size at least 24 by 24 px (aim for 44) | 2.5.8 | pad small controls; space neighbours |
| No action needs dragging or complex gestures only | 2.5.7, 2.5.1 | offer a button alternative |
| Time limits can be extended; warn first | 2.2.1 | time-out warning with "Stay signed in" |
| Nothing flashes; motion can be turned off | 2.3.1, 2.3.3 (AAA, do it anyway) | `prefers-reduced-motion` |

## Understand and recover

| Check | Criterion | How to meet it |
| --- | --- | --- |
| Labels and instructions are visible | 3.3.2 | label above each field, format hints |
| Errors are identified in text and say how to fix | 3.3.1, 3.3.3 | message next to the field, `aria-invalid`, summary |
| Legal and financial actions can be checked, corrected or reversed | 3.3.4 | review screen before committing |
| Do not ask for the same information twice | 3.3.7 | carry values forward |
| Signing in or approving does not depend on memory or a puzzle | 3.3.8 | allow paste and password managers, offer device approval |
| Help is in the same place on every screen | 3.2.6 | one consistent help link |
| Nothing unexpected happens on focus or input | 3.2.1, 3.2.2 | change screens only on an explicit action |
| Status messages are announced without moving focus | 4.1.3 | `role="status"` for progress and results, `role="alert"` for errors |

Passing these checks is evidence, not proof, of accessibility. Record what was checked and how.
