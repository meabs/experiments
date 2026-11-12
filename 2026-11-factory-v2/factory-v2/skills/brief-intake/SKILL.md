---
name: brief-intake
description: Stage 1. Turn a brief into users, goal, constraints, assumptions and success measures before any research or design.
---

# Brief intake

**Read first:** `okf/rules/house-rules.md`, `okf/rules/unattended.md`.
**Writes:** `design/01-brief.md` (about 200 to 300 words).

## Steps

1. Restate the brief in two sentences: who it is for and what they are trying to get done. If you cannot, the brief
   is unclear; say where.
2. Name the users. Two or three real situations, not personas with hobbies: "paying a builder for the first time,
   on a phone, slightly anxious about the amount". Include one person who finds this harder than most (low vision,
   one hand, poor signal, stressed, not confident with money or English).
3. List what the brief fixes (brand, platform, data, screens it names) and what it leaves open.
4. Decide what applies:
   - industry: is there a folder under `okf/industry/`? Then its skill is required.
   - legal: personal data, consent, prices, credit, claims, cancelling? Then `legal-review` is required.
   - accessibility-review always applies.
5. Write 3 to 5 success measures a reviewer could check on the prototype ("a first-time user can tell the payment
   has not gone yet", not "intuitive").
6. Write open questions and, when working without a person, the assumption you made for each.

## Output shape

```
# Brief: <name>
## In two sentences
## Who and when (situations)
## Fixed by the brief / left open
## Applies: industry, legal, accessibility
## Success measures
## Open questions and assumptions
```

## Done when

Someone who has not read the brief could design the right thing from this file alone.
