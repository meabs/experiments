---
name: impeccable
description: Design craft guidance from Impeccable (Apache-2.0) for app UI - the quality floor and the things to refuse, Operate-mode depth, and per-topic passes (layout, type, colour, copy, edge cases, adaptation, empty states, simplifying, polish, audit, heuristic critique). Use inside stages 3 to 6 to make a design look deliberate rather than generic.
license: Apache-2.0 (see LICENSE and NOTICE.md in this folder)
---

# Impeccable (craft layer)

This skill brings the guidance from [Impeccable](https://github.com/pbakaus/impeccable) (Paul Bakaus, Apache-2.0, commit
`b4bff16`) into the factory. It exists to push work past the generic look: clear hierarchy, a deliberate system, no
default patterns, every state designed. The files in `reference/` are Impeccable's own, with its command-line tool,
live browser mode and project files removed (see the header in each file). The licence and its notice are in this
folder. Impeccable's detector and live mode are **not** included; use `tools/lint_prototype.py` and the checks in
`okf/rules/quality-bar.md` instead.

## Precedence

When this skill and the factory disagree, the factory wins, in this order:

1. The brief, then `okf/rules/` (house rules, quality bar), then the industry pack (for banking, `okf/industry/banking/`).
2. The accessibility and legal skills and knowledge.
3. This skill.

Known overrides for banking and other money screens (Impeccable's "refuse" list calls these defaults, and its own
rule is that the brief and the product's conventions win):

- A large balance or amount with a small label is **required** on money screens (`money-and-trust.md`). Do not
  replace it to avoid the "hero metric" pattern; do make it exact, well set and unique in treatment.
- Status colours, tags and tabular figures are standard banking components, not decoration.
- Use Impeccable's **Operate** mode (the visitor is completing a task) for every app screen, and **Read** mode for
  help and article content. Persuade and Experience modes (landing pages, portfolios) do not apply to app journeys.
- "Familiarity is a feature" in Operate mode: use standard patterns for standard tasks, and spend the design effort
  on hierarchy, spacing, type, one considered accent and the details.

## Where to use it

| Stage | Read | Use it to |
| --- | --- | --- |
| 3 Storyboard | [shape](reference/shape.md) | plan the UX before drawing: users, flow, content and states |
| 4 Visual direction | [operate](reference/operate.md), the "Refuse" list in [craft-floor](reference/craft-floor.md), then [typeset](reference/typeset.md), [colorize](reference/colorize.md), [layout](reference/layout.md) as needed | choose a direction that is specific to this product and avoids the category's defaults; write it into the tokens |
| 5 Prototype | [craft-floor](reference/craft-floor.md) **before the first UI edit**; [operate](reference/operate.md); [clarify](reference/clarify.md) for copy; [onboard](reference/onboard.md) for empty and first-use states; [ios](reference/ios.md) or [android](reference/android.md) only if the brief asks for a native look | build to the floor: contrast, depth, spacing, type, motion, states, browser surfaces, copy |
| 6 Critique | [critique-reference](reference/critique-reference.md), [audit](reference/audit.md), then fix with [polish](reference/polish.md), [harden](reference/harden.md), [adapt](reference/adapt.md), [distill](reference/distill.md) | score the design, find what is generic or fragile, fix the worst first |

## How to apply it

1. **Look at the rendered result** at 390 px and 320 px wide when a browser or screenshot tool is available; batch
   the checks, then fix, then look again. If you cannot render it, say so in the review.
2. **Floor before taste.** Run the "Verify" list in `craft-floor.md` on the built result. Then spend the remaining
   effort on the committed direction (the one sentence in `design/04-direction.md`).
3. **Refuse the defaults deliberately.** For each item in the "Refuse" list, either do not do it or write down in the
   direction file why this product earns it (for example the balance amount).
4. **The design review is mandatory.** **Critique with the heuristics.** In stage 6, score the ten usability heuristics 0 to 4, run the cognitive-load
   checklist, and walk the journey as at least three of the personas in `critique-reference.md` (always the
   accessibility-dependent and the distracted mobile users; add the confused first-timer for money journeys). Use
   the users in `design/01-brief.md` for any project-specific persona.
5. **Fix in order.** Broken or blocked tasks first, then missing states, then hierarchy and consistency, then polish
   (`polish.md` step 3). Record what was fixed and what was not in `design/05-review.md`.

## Not included

Impeccable's `detect` rules (59 checks run by its own binary), live variant mode, hooks, `init`/`document` project
files and its critique sub-agent orchestration. Its guidance that depends on them was removed from the vendored
files. Do not try to run an `impeccable` command; none exists here.
