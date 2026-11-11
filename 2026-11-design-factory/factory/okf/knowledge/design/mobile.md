---
type: Playbook
title: Mobile patterns
description: Phone-first layout - thumb reach, navigation, bottom actions, on-screen keyboards, safe areas and small or zoomed screens.
tags: [design, mobile]
status: draft
---

# Mobile patterns

- **Design at 390 px, check at 320 px.** Nothing scrolls sideways. Long words and amounts wrap or shrink gracefully
  (`overflow-wrap: anywhere` on user content, `min-width: 0` on flex children).
- **Thumb reach.** Primary actions in the lower half; navigation and rarely used actions at the top. Destructive
  actions are not next to the primary one.
- **Targets.** At least 44 by 44 px with 8 px between neighbours. Make whole rows pressable.
- **Navigation.** In a task journey, hide the app's tab bar; show back or close and the step. On overview screens, a
  bottom tab bar with 3 to 5 labelled items, the current one marked with more than colour (`aria-current="page"`).
- **Bottom action bar.** Use `position: sticky; bottom: 0` inside the screen, with a solid surface and padding for
  the home indicator (`env(safe-area-inset-bottom)`). It must never cover the focused field or error messages.
- **Keyboards.** Choose with `inputmode`. Keep the field and its label visible when the keyboard is open. One field
  per screen for big, important inputs such as an amount.
- **Scrolling.** One scroll direction. No scroll areas inside scroll areas. Important content is not hidden in
  carousels.
- **Text size.** Sizes in rem so the user's setting is respected. Do not set `maximum-scale` or
  `user-scalable=no`. Layout holds at 200% text.
- **Sheets over dialogs** for short choices on a phone; full screens for anything with a form.
- **Motion.** 150 to 250 ms, ease-out, to show where something came from. Nothing that loops. Remove it under
  `prefers-reduced-motion: reduce`.
- **Desktop.** The same column centred with a maximum width, on a quiet page background. It should look intended, as
  a phone-first product does on a laptop.
