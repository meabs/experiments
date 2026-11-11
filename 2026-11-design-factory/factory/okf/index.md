---
okf_version: "0.2"
---

# Design Factory knowledge index

Maintained by the design and front-end team. This index is the one place that lists the factory's workflow, skills,
rules and knowledge. If something is not listed here, it is not part of the factory.

Links starting with `/` are relative to this `okf/` folder. Skills live in `../skills/<name>/SKILL.md`.

## 1. Workflow (read first)

- [Workflow](/workflow.md) - the six stages from brief to handoff, what each one must write, and the check that ends
  each stage. Read before any work.

## 2. Rules (apply to all work)

- [House rules](/rules/house-rules.md) - honesty about evidence, fictional data, no compliance claims, language and
  file conventions.
- [Quality bar](/rules/quality-bar.md) - what "good" means here for a screen and for a journey; the checks every
  prototype must pass before it is called finished.
- [Working without a person](/rules/unattended.md) - what to do when nobody is there to answer questions or approve a
  stage.

## 3. Skills

Read the skill's file before doing that kind of work. Each skill says what to read, what to do and what to write.

### Workflow skills (one per stage, in order)

| Stage | Skill | Use it to |
| --- | --- | --- |
| 1 | [brief-intake](../skills/brief-intake/SKILL.md) | turn the brief into users, goals, constraints, assumptions and success measures |
| 2 | [design-research](../skills/design-research/SKILL.md) | find out what users need, what conventions exist and what can go wrong, without inventing evidence |
| 3 | [journey-storyboard](../skills/journey-storyboard/SKILL.md) | draw the journey as frames: main path, branches, failure and recovery, and the list of screens and states |
| 4 | [visual-direction](../skills/visual-direction/SKILL.md) | choose one deliberate look: type, colour, spacing, shape, components, written as tokens |
| 5 | [prototype-build](../skills/prototype-build/SKILL.md) | build the screens and states as a working front-end prototype from the tokens |
| 6 | [design-critique](../skills/design-critique/SKILL.md) | review the built prototype as a designer would, fix the worst problems, and write the handoff |

### Specialist skills (used inside the stages above)

| Skill | Use it when |
| --- | --- |
| [content-design](../skills/content-design/SKILL.md) | writing any words on a screen: headings, labels, buttons, errors, confirmations |
| [accessibility-review](../skills/accessibility-review/SKILL.md) | designing and checking any screen (WCAG 2.2 level AA is the target) |
| [legal-review](../skills/legal-review/SKILL.md) | the journey collects personal data, asks for consent, sells or prices something, or makes a claim |
| [banking-design](../skills/banking-design/SKILL.md) | the brief is for a bank, payment, savings, lending or card product (industry skill) |
| [frontend-handoff](../skills/frontend-handoff/SKILL.md) | writing notes for the developers who will build the real thing |

## 4. Knowledge

Read only what the brief needs.

### Design

- [Visual hierarchy and layout](/knowledge/design/hierarchy-and-layout.md) - one main thing per screen, spacing scale,
  alignment, grouping.
- [Typography and colour](/knowledge/design/type-and-colour.md) - type scale, weights, colour roles, contrast pairs,
  dark text on light surfaces.
- [Components and states](/knowledge/design/components-and-states.md) - buttons, fields, lists, cards, sheets; the
  states every component and screen needs.
- [Forms](/knowledge/design/forms.md) - one question per step, labels, hints, validation, error recovery.
- [Mobile patterns](/knowledge/design/mobile.md) - thumb reach, navigation, bottom actions, keyboards, safe areas.

### Accessibility

- [WCAG 2.2 AA checklist](/knowledge/accessibility/wcag-22-aa.md) - the criteria that design and front-end work most
  often fails, each with how to meet it.
- [Keyboard, focus and screen readers](/knowledge/accessibility/keyboard-and-semantics.md) - native elements first,
  focus order, visible focus, names and roles, live messages, screen changes.

### Legal (UK)

- [Privacy, consent and cookies](/knowledge/legal/privacy-and-consent.md) - UK GDPR and PECR points that change a
  screen.
- [Fair choices and clear prices](/knowledge/legal/fair-choices.md) - misleading or pressuring design, prices,
  cancelling, accessibility duties under the Equality Act.

### Industry: banking (UK retail)

- [Banking index](/industry/banking/index.md) - start here for any banking brief. Lists the files on money and trust,
  payments, savings, borrowing, cards and security, customers in vulnerable circumstances, and the regulated
  information a screen must carry.

Other industries are added as a new folder under `industry/` with its own index and one industry skill.

## 5. Tools

- `python3 tools/contrast.py "#1a1a2e" "#ffffff"` - contrast ratio of two colours and whether it passes AA.
- `python3 tools/lint_prototype.py <folder>` - quick structural checks on a built prototype (page language, title,
  viewport, field labels, button names, image alternatives, heading order, token contrast). It does not replace the
  accessibility review.
- `python3 tools/check_bundle.py` - checks this index lists every skill and knowledge file and that links resolve.
  Run it after changing the factory itself.
