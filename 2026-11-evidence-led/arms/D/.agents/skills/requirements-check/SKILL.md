---
name: requirements-check
description: Use at the start of a ticket to list every requirement, and again before finishing to check each one is met.
---

# Requirements check

## At the start

1. Read the whole ticket. Write down, as a numbered list:
   - every endpoint, field, status code and value it names;
   - every rule, including limits, rounding, ordering, defaults and error cases;
   - every existing behaviour it says must keep working.
2. Read the code the ticket touches. Add to the list any constraint the code already enforces that your change must
   respect (validation, permissions, how similar features are built).
3. Where the ticket is ambiguous, choose the reading most consistent with the rest of the ticket and the existing code,
   and note the choice.

## Before finishing

1. Go through the list one item at a time and point to the code (and, where there is one, the test) that meets it.
2. Anything not met: fix it, or say in your summary that it is not done and why.
3. Mention any ambiguity you resolved and how.
