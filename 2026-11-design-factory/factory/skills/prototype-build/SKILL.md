---
name: prototype-build
description: Stage 5. Build every screen and state from the storyboard as a working, offline front-end prototype using the direction's tokens, semantic HTML and accessible components.
---

# Prototype build

**Read first:** `design/03-storyboard.md`, `design/04-direction.md`, `okf/knowledge/design/components-and-states.md`,
`okf/knowledge/design/forms.md`, `okf/knowledge/design/mobile.md`,
`okf/knowledge/accessibility/keyboard-and-semantics.md`. Use `content-design` for every word.
**Before the first screen**, read `skills/impeccable/reference/craft-floor.md` and `operate.md` and build to the floor; run its "Verify" list on the finished result, together.
**Writes:** `prototype/` (or the folder the brief names).

## Default form

Unless the brief asks for a framework: plain HTML, CSS and JavaScript, no build step, no network. One `index.html`,
one stylesheet and one script is enough (they may be inline if the brief asks for a single file). Mobile first at
390 px wide; it must also work at 320 px and look intentional on a desktop (a centred column, not stretched).

## Steps

1. **Tokens.** Paste the `:root` token block. Every colour, size, space and radius in the CSS uses a variable.
2. **Base.** `<html lang="en-GB">`, a `<title>`, `<meta name="viewport" content="width=device-width, initial-scale=1">`
   (never disable zoom), `box-sizing: border-box`, the system font stack, sizes in rem, line height about 1.5 for
   body text.
3. **Components before screens.** Build the core components from the direction once, with all their states (default,
   hover, focus-visible, pressed, disabled, error), then compose screens from them.
4. **Screens.** One `<section>` (or `<main>` content) per screen id from the storyboard, each with exactly one `<h1>`.
   Show one screen at a time. Make each screen directly reachable by address (`index.html#review`) and by using the
   journey. When the screen changes, move focus to the new screen's `<h1>` (give it `tabindex="-1"`) and update the
   page title.
5. **States.** Build every state in the storyboard list: errors, empty, loading or waiting, declined, success. If a
   state only appears after a system answer, simulate the answer (a short delay, a test value that triggers it) and
   also make it reachable by address (for example `#review-error`) so reviewers can see it.
6. **Forms.** Follow `forms.md`: visible labels, hints tied with `aria-describedby`, the right `type`, `inputmode`
   and `autocomplete`, validation on submit, an error summary plus messages next to fields, values kept on return.
7. **Behaviour.** Real navigation between screens, back keeps data, the primary button cannot fire twice, amounts and
   names typed earlier appear on later screens.
8. **Check.** Run `python3 tools/lint_prototype.py prototype` and fix every finding. Walk the storyboard list and tick
   each screen and state.

## Do not

- Leave dead buttons, placeholder text or screens that exist only as a heading.
- Use `div` or `span` as buttons or links. Use `<button>` for actions and `<a href>` for navigation.
- Remove focus outlines, use placeholder text as the label, or fix heights on text containers.
- Load fonts, icons, images or scripts from the network. Draw icons as inline SVG with `aria-hidden="true"` and a
  text label beside them.
