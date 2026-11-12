---
type: Rule
title: House rules
description: Rules that apply to all factory work - honesty about evidence, fictional data, no compliance claims, conventions.
tags: [rules]
status: draft
---

# House rules

## Evidence

1. Never invent evidence. No made-up interviews, usability tests, survey numbers, analytics, quotes or citations. If
   you did not do a study, do not describe one.
2. Label every research finding with where it comes from: **brief** (stated in the brief), **factory** (a knowledge
   file here, named), **convention** (common practice you know of, named products only if you are sure), **reasoning**
   (your own inference) or **source** (a document you actually read in this session, with its address).
3. Write unknowns down as questions for the team. A good list of what we don't know is a research result.

## Claims

4. Never write that a design "is compliant", "meets WCAG", "is approved" or "is legally reviewed". Say what was
   checked, how, and what was not checked. Only people sign off compliance.
5. Legal and regulatory wording in a prototype is **draft for review**. Use the points in the knowledge files to put
   the right information in the right place; mark anything you are unsure of in the review file.
6. Report checks honestly: run, passed, failed or not run. A check you could not run is "not run", with the reason.

## Content and data

7. Use fictional brands, people, account numbers and data. Never copy a real company's logo, name, typeface licence
   or distinctive look. Sort codes and account numbers must be obviously fake but correctly shaped.
8. British English, plain words, sentence case. Money as `£1,250.00`. Dates as `12 November 2026`.
9. No placeholder text ("Lorem ipsum", "Button", "Title here") in anything delivered. Every word on a screen is
   a design decision.

## Building

10. Decide before building: research, storyboard and visual direction files exist before the first screen is coded.
11. Design tokens first: colours, type sizes, spacing, radius and shadow are named variables. No one-off values in
    components.
12. Every screen in the storyboard gets built, including the unhappy ones. An error, empty, loading or waiting state
    that was drawn but not built is a defect.
13. Prototypes run offline from a folder: no build step, no network requests, no external fonts, images or scripts
    unless the brief asks for a framework.
14. Do not edit files under `okf/`, `skills/` or `tools/` during project work. Suggest factory changes in the handoff
    file under "Factory feedback".
