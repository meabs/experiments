---
type: Playbook
title: Components and states
description: The core components of an app prototype and the states every component and every screen needs.
tags: [design, components]
status: draft
---

# Components and states

## Every screen has states

Before building a screen, list which of these it has. Most have at least four.

| State | What it shows |
| --- | --- |
| Default | the normal case with realistic content |
| Loading or waiting | what is happening and, if over a few seconds, that it is still working; skeletons for content, a labelled spinner for actions |
| Empty | nothing yet: say why and offer the first step |
| Partial or long | very long names, big amounts, many rows, one row |
| Error (input) | which fields, what is wrong, how to fix |
| Error (system) | what failed, whether anything changed, what to do now, a way to try again or get help |
| Success | what happened and what happens next |
| Pending or uncertain | the system does not know yet: say so, say what not to do, say how they will find out |
| Blocked or not allowed | why, and the route that is allowed |
| Offline or timed out | what was kept, how to carry on |

## Every interactive component has states

Default, hover, focus-visible, pressed, disabled, and (for inputs) filled, error. Build them once.

## Core components

- **Primary button.** Filled, full width on phones, at least 48 px high, verb plus object. One per screen. While
  working it shows a label like "Sending..." and cannot be pressed again.
- **Secondary button.** Outline or tonal. **Tertiary.** Text only, still a 44 px target.
- **Destructive action.** Not red-filled by default. Ask for confirmation that repeats what will be lost.
- **Text field.** Label above, hint below the label, input at least 48 px high with a visible edge (3:1), error
  message below with an icon and text. Width suggests the expected length.
- **Choice.** Radios for one of a few (show all options), a checkbox for an independent yes or no, a switch only for
  settings that apply at once. Whole row is the target.
- **List row.** Leading icon or avatar (optional), primary text, secondary text, trailing value or chevron. If the
  row navigates, the whole row is one link or button.
- **Card.** A surface grouping related content with one purpose. Not every block needs a card.
- **Banner or panel.** Information, success, warning, error: icon, a short heading, one or two sentences, optional
  action. Different in shape or icon as well as colour.
- **Sheet or dialog.** For a short decision without leaving the screen. Has a heading, traps focus, closes with
  Escape and a visible close button, returns focus to where it came from.
- **Header.** Back (previous step) or close (leave the journey), never both meaning the same thing. Progress as
  "Step 2 of 4" in text.
- **Bottom action bar.** Holds the primary action; does not cover content or the focused field.
- **Result panel.** Icon, heading that states the outcome, key facts, what happens next, one next action.

## Feedback timing

Under a tenth of a second: no indicator. Up to a second: disable the control and show a label. Longer: explain. Over
10 seconds or unknown: let the person leave safely and say how they will be told.
