---
type: Playbook
title: Forms
description: Structure, labels, hints, validation and error recovery for forms in app journeys.
tags: [design, forms]
status: draft
---

# Forms

## Structure

- Ask only what is needed for this journey. Every extra field costs completions.
- One topic per screen on a phone ("Who are you paying?", then "How much?"). Short related fields can share a screen.
- Order as in a conversation. Put the easy, expected questions first.
- Show progress in words for journeys over three steps. Let people go back without losing anything.
- Do not make people enter the same thing twice in one journey; carry it forward.

## Fields

- A visible `<label for>` on every field, above the field. Placeholder text is not a label and is best left empty.
- Hint text between the label and the input, tied with `aria-describedby`: format, where to find it, why it is asked.
- The right keyboard and help: `type="email"`, `inputmode="numeric"` for digits (not `type="number"` for codes,
  account numbers or money), `inputmode="decimal"` for amounts, `autocomplete` values (`name`, `email`, `tel`,
  `postal-code`, `one-time-code`).
- Accept what people type: spaces and hyphens in sort codes, a pound sign in amounts, lower case postcodes. Format it
  for them afterwards.
- Field width matches the answer. Group radio options in a `fieldset` with a `legend`.
- Mark the optional fields "(optional)" rather than starring the required ones.

## Validation

- Validate when the person submits the step, not while they are still typing. After a first failed submit, clear each
  error as it is fixed.
- On failure: keep everything typed; show an error summary at the top (`role="alert"`, focus moved to it, each item a
  link to its field); show the message next to the field, tied with `aria-describedby`, and set `aria-invalid="true"`.
- Messages say how to fix it, specific to the field: "Enter an amount, like 25.00", "Account number must be 8
  digits". Not "Invalid" or "Required".
- Do not disable the submit button to signal an incomplete form; let people press it and learn what is missing.

## Review and commit

- Before anything costly or hard to undo: a review screen listing each answer with a "Change" link that returns to
  that step and comes back.
- The commit button states the consequence. After pressing it, lock it and show progress.
- After success, a result screen (not a toast) with a reference and what happens next.

## Sensitive input

Mask only what must be hidden, offer "Show". Never block paste. Do not ask people to remember or transcribe codes
when the device can pass them. Give enough time, warn before a time-out and let them extend it.
