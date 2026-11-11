---
name: design-research
description: Stage 2. Desk research for a brief - user needs, existing conventions, risks and regulated information - with every finding labelled by source and turned into a design consequence. Never invents evidence.
---

# Design research

**Read first:** `design/01-brief.md`; the industry index if one applies (for example `okf/industry/banking/index.md`)
and the files it points to for this journey; `okf/knowledge/legal/` files if legal-review applies.
**Writes:** `design/02-research.md` (about 300 to 450 words).

## Steps

1. **Jobs and worries.** For each situation in the brief, write what the person is trying to do and what they are
   worried about at that moment. Worries drive design more than features do.
2. **Conventions.** What do people already expect from this kind of journey (order of steps, names of things, where
   the main action sits)? Follow conventions unless there is a reason not to; note the reason.
3. **What goes wrong.** List the real failures: wrong input, the system saying no, the system being slow or down, the
   person changing their mind, the person being tricked, doing it twice by accident.
4. **What must be shown.** From the industry and legal files: information the screens must carry, where and when
   (before commitment, at review, after).
5. **Turn each finding into a consequence.** Every line ends "-> so the design should ...". A finding with no
   consequence is cut.
6. **Unknowns.** What would you ask five real users or the product owner? These go to the team.

## Rules

- Label each finding: (brief), (factory: file name), (convention), (reasoning) or (source: address). See house rule 2.
- No invented studies, numbers, quotes or competitor details. If you can browse and the brief allows it, read primary
  sources and cite them; if you cannot, say "desk research from factory knowledge only; no sources fetched".
- Research ends in decisions. Finish with "The five things this changes in the design".

## Output shape

```
# Research: <name>
Method: <what you actually did, one line>
## Jobs and worries
## Conventions to follow (and any to break)
## What goes wrong
## What the screens must show
## Unknowns for the team
## The five things this changes in the design
```
