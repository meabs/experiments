---
type: Playbook
title: Keyboard, focus and screen readers
description: Building prototype screens that work with a keyboard and a screen reader - native elements, focus management in single-page prototypes, names, live messages and dialogs.
tags: [accessibility, front-end]
status: draft
sources:
  - title: WAI-ARIA Authoring Practices Guide
    resource: https://www.w3.org/WAI/ARIA/apg/
    checked: patterns written from the guide as known to the author; confirm against the guide for custom widgets
---

# Keyboard, focus and screen readers

## Native first

`<button>` for actions, `<a href>` for going somewhere, `<input>`, `<select>`, `<textarea>` with `<label>`,
`<fieldset>` and `<legend>` for groups, `<dialog>` or a well-built sheet, `<details>` for show and hide. A `div` with
a click handler is not a button: it has no role, no focus and no keyboard support. Use ARIA only to add what HTML
cannot say.

## Page skeleton

```html
<html lang="en-GB">
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
  <header>...</header>
  <main id="main">
    <section id="review" aria-labelledby="review-h">
      <h1 id="review-h" tabindex="-1">Check the details</h1>
      ...
    </section>
  </main>
</body>
```

## Screen changes in a one-page prototype

When the visible screen changes, a screen reader user hears nothing unless you tell them. On every change:

1. hide the old screen with the `hidden` attribute (not just off-screen or transparent);
2. show the new one, set `document.title` ("Check the details - Brand");
3. move focus to the new screen's `h1` (`tabindex="-1"`, then `.focus()`), and scroll to the top;
4. keep the browser's back button working (`hashchange` or the History API).

## Focus

- Visible on every focusable thing, on every surface: `:focus-visible { outline: 3px solid var(--focus);
  outline-offset: 2px; }`. Check the ring against both light and coloured backgrounds.
- Order follows the source. No positive `tabindex`. Hidden screens and closed sheets contain nothing focusable (the
  `hidden` attribute or `inert`).
- Dialogs and sheets: focus moves in on open (to the heading or first control), Tab cycles inside, Escape closes,
  focus returns to the opener. `role="dialog"`, `aria-modal="true"`, `aria-labelledby`.

## Names and descriptions

- Visible label text is the accessible name. Icon-only button: `aria-label="Close"`. Decorative SVG:
  `aria-hidden="true" focusable="false"`.
- Repeated links get distinguishing hidden text: `Change<span class="visually-hidden"> amount</span>`.
- Hints and errors: `aria-describedby="amount-hint amount-error"`; invalid fields `aria-invalid="true"`.
- Label and value pairs (a review summary) as `<dl>`, `<dt>`, `<dd>`.
- Amounts read better with text: `£1,250.00` is fine; avoid splitting pounds and pence into separate elements
  without a combined hidden text.

## Messages that appear

- Result of an action without a screen change (name checked, saved, sending): put it in a container that already
  exists in the page with `role="status"`; change its text.
- Errors needing attention now: `role="alert"`, or move focus to an error summary that has `tabindex="-1"`.
- Loading: set `aria-busy="true"` on the region and give the spinner text ("Checking the name...").

## Visually hidden helper

```css
.visually-hidden { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden;
  clip: rect(0 0 0 0); white-space: nowrap; border: 0; }
```
