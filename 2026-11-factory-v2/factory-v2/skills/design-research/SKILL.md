---
name: design-research
description: Stage 2. Desk research for a brief - user needs, existing conventions, risks and regulated information - with every finding labelled by source and turned into a design consequence. Never invents evidence.
---

# Design research

**Read first:** `design/01-brief.md`. Do not read the industry pack or the legal files at this stage: they are applied to the
chosen concept after stage 2b. Use the web and your own knowledge.
**Ends with:** a numbered Decisions list (R1, R2, ...): the choices the design will take from this research.
**Writes:** `design/02-research.md` (about 350 to 500 words), or the research file the brief names.

## Steps

1. **Jobs and worries.** For each situation in the brief, write what the person is trying to do and what they are
   worried about at that moment. Worries drive design more than features do.
2. **Conventions.** What do people already expect from this kind of journey (order of steps, names of things, where
   the main action sits)? Note them. They are defaults, not requirements: say which ones the product could break and
   what that would give people.
3. **What goes wrong.** List the real failures: wrong input, the system saying no, the system being slow or down, the
   person changing their mind, the person being tricked, doing it twice by accident.
4. **What must be shown.** Only what you already know or found on the web is needed here; the industry and legal files
   are applied in stages 3 to 6.
5. **Trends and styles.** What visual, layout, interaction and content styles are current for this kind of product
   (for example in banking and fintech apps), and what is changing? If you can search the web, do it: read several
   current sources (design write-ups, product teardowns, regulators' or standards bodies' pages for rules), note each
   address and date, and say what you saw rather than what you assume. For each trend decide: adopt, adapt or avoid for
   this brief, and why (fit with the users and their worst moment, accessibility, trust, the industry pack). A trend
   is not a reason on its own, and copying a real company's look is out. If you cannot search, say so and work from
   the factory knowledge and your own knowledge, labelled as such.
6. **Turn each finding into a consequence.** Every line ends "-> so the design should ...". A finding with no
   consequence is cut.
7. **Unknowns.** What would you ask five real users or the product owner? These go to the team.

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
## Trends and styles (with sources, and adopt / adapt / avoid)
## What goes wrong
## What the screens must show
## Unknowns for the team
## Decisions (R1, R2, ...)
Numbered. Each: what the design will do, why (which finding), and the frame or token where it should show.
## The five things this changes in the design
```
