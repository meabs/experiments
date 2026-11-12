---
name: banking-design
description: Industry skill for UK retail banking briefs - payments, savings, borrowing, cards and account screens. Applies banking conventions, trust and fraud patterns, regulated information and care for customers in vulnerable circumstances at each stage.
---

# Banking design (industry skill)

**Order.** Do not read this skill until the concept (stage 2b) is chosen. It is a lens for stages 3 to 6, applied to the chosen
concept: it decides how the concept is built safely, not whether it is built.

**Read first:** `okf/industry/banking/index.md`, then only the files it lists for this journey.

## What to do at each stage

**Research (stage 2).** From the journey file (payments, savings, borrowing, cards): the conventional order of steps,
the system answers that can come back, the fraud and mistake risks, and the information that must be shown. From
`vulnerable-customers.md`: who is likely to struggle with this journey and what would help.

**Storyboard (stage 3).** The storyboard is about the chosen concept. Add a banking safeguard frame only where the concept
touches that safeguard, one frame each, and do not add a payment journey unless the concept is about payments. Banking
frames people forget, to use where they apply:
- a review step before anything that moves money or creates a commitment;
- every system answer as its own frame (name check results, declined, held for checks, limit reached, pending);
- an approval step (strong customer authentication) where the journey file says one is needed, simulated;
- "what if this is a scam or a mistake?" and "I need help" routes;
- a result frame that says what happened to the money and what happens next.

**Direction (stage 4).** Apply `money-and-trust.md`: amounts are the largest thing on a money screen, set in tabular
figures; one calm brand colour; red only for real danger; warnings look different from errors and from marketing.

**Build (stage 5).** Use the banking components in `money-and-trust.md` (amount display, account row, payee row,
transaction row, review summary, warning panel, result panel). Put regulated information from
`regulated-information.md` in the body of the screen where the decision is made. Mask what should be masked.

**Critique (stage 6).** Run this checklist and record it in the review:

1. Can the person always see which account money leaves and how much is in it?
2. Before money moves: are the recipient, amount, date and any fee repeated on one review screen?
3. Is every system answer shown in plain words with what to do next, including whether money has left?
4. Is there a fraud or scam check at the risky moment, specific to the situation, that cannot be mistaken for
   marketing and does not blame the customer?
5. Is the regulated information for this product present, readable and before commitment?
6. Could someone under pressure, in a hurry or new to banking get through without harm? Is help from a person easy
   to find?
7. Are amounts, dates, account numbers and names formatted the banking way, with no ambiguity?
8. Does the confirm button say exactly what will happen ("Send £250.00")? Is double-sending prevented?
9. Is anything shown that should be masked, or masked that the person needs to check?
