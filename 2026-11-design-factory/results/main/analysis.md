# Analysis: main

60 runs, 30 pairs (plain run i with factory run i of the same brief). A = plain agent, B = Design Factory.

## Which design do the judges prefer?

Each pair gets a score from 0 to 1: the share of its judge votes (two judges, two orders) that chose the factory's design; a tie counts half. Above 0.5 the factory wins the pair, below 0.5 the plain agent does. 0.5 overall means no preference. p is a two-sided sign-flip permutation test on the pair scores; the sign test counts wins only.

| Question | Pairs | Factory wins | Plain wins | Split | Mean score (95% CI) | p | Holm p | Sign test p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 whole design | 30 | 14 | 11 | 5 | 0.53 (0.39 to 0.66) | 0.8015 | 0.8015 | 0.6900 |
| H2 looks only (first six screens) | 30 | 6 | 21 | 3 | 0.32 (0.19 to 0.45) | 0.0154 | 0.0308 | 0.0059 |

### By criterion (mean pair score; above 0.5 favours the factory; descriptive)

| Criterion | Whole design | Looks only |
| --- | --- | --- |
| overall | 0.53 | 0.32 |
| hierarchy | 0.40 | 0.32 |
| polish | 0.44 | 0.37 |
| identity | 0.13 | 0.14 |
| content | 0.66 | 0.50 |
| trust | 0.72 | 0.51 |
| journey | 0.72 | - |

### By brief (mean pair score; factory wins-plain wins-split)

| Brief | Whole: score | Whole: W-L-S | Looks: score | Looks: W-L-S |
| --- | --- | --- | --- | --- |
| D1 | 0.70 | 3-0-2 | 0.15 | 0-4-1 |
| D2 | 0.45 | 2-2-1 | 0.25 | 1-4-0 |
| D3 | 0.90 | 5-0-0 | 0.55 | 2-2-1 |
| D4 | 0.45 | 2-3-0 | 0.25 | 1-4-0 |
| D5 | 0.35 | 1-3-1 | 0.40 | 1-3-1 |
| D6 | 0.30 | 1-3-1 | 0.30 | 1-4-0 |

### The judges

Chose the first design shown: 50% means no position bias. Same choice in both orders: how often a judge picked the same design whichever came first (a pair where it flips counts as a split).

| Judge | Calls | Chose the design shown first | Same choice in both orders | Mean vote for factory |
| --- | --- | --- | --- | --- |
| google/gemini-4-argon | 120 | 68% | 63% | 0.42 |
| anthropic/claude-sonnet-5.5 | 120 | 51% | 82% | 0.42 |

The two judges reached the same pair result (factory, plain or split) in 62% of 60 pair-views.

## Checklist, accessibility checks

Checklist: share of the brief's 12 checklist items visible in the storyboard's text (higher is better). axe: WCAG A and AA rule violations found by axe-core per screen (lower is better). Difference = factory minus plain, per pair.

| Measure | Pairs | Plain | Factory | Difference (95% CI) | p | Holm p |
| --- | --- | --- | --- | --- | --- | --- |
| H3 checklist items present (share of 12) | 30 | 0.59 | 0.85 | +0.26 (+0.19 to +0.32) | 0.0001 | 0.0004 |
| H4 axe rule violations per screen (lower is better) | 30 | 1.00 | 0.06 | -0.94 (-1.11 to -0.77) | 0.0001 | 0.0004 |

## Does the design apply the research?

A vision model (blind to the arm) reads each run's research.md and looks at its frames. Decisions listed = the numbered design decisions the agent wrote; applied = visibly shown in a frame (higher is better); a run that listed no decisions scores 0. Specific = names current trends or styles with sources.

| Arm | Runs | Decisions listed per run | Share applied | Research is specific |
| --- | --- | --- | --- | --- |
| Plain | 30 | 7.9 | 81% | 100% |
| Factory | 30 | 4.5 | 68% | 73% |

| Measure | Pairs | Plain | Factory | Difference (95% CI) | p | Holm p |
| --- | --- | --- | --- | --- | --- | --- |
| H6 research decisions visibly applied in the storyboard (share) | 30 | 0.81 | 0.68 | -0.13 (-0.29 to +0.03) | 0.1416 | 0.2832 |

### Descriptive measures (means over runs; no tests)

| Measure | Plain | Factory |
| --- | --- | --- |
| Checklist: 'state' items present | 67% | 88% |
| Checklist: 'info' items present | 46% | 85% |
| Screens delivered | 7.3 | 9.7 |
| Delivery contract met (screens.json and every screen opens) | 100% | 100% |
| Screens with no axe violation | 10% | 94% |
| Screens that scroll sideways at 320 px (lower is better) | 50% | 7% |
| Controls at least 24 px in both directions | 70% | 95% |
| Controls at least 44 px in both directions | 51% | 92% |
| Screens with exactly one h1 | 77% | 80% |
| Clickable things not reachable by keyboard, per run (lower is better) | 2.3 | 0.5 |
| Console errors per run (lower is better) | 0.0 | 0.2 |

### By brief

| Brief | Checklist of 12: plain | factory | axe per screen: plain | factory | Screens: plain | factory |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | 7.8 | 11.4 | 1.00 | 0.01 | 10.2 | 14.0 |
| D2 | 4.6 | 10.0 | 1.20 | 0.17 | 8.4 | 10.2 |
| D3 | 6.8 | 11.0 | 0.80 | 0.09 | 8.4 | 12.4 |
| D4 | 7.4 | 9.4 | 1.00 | 0.00 | 7.8 | 9.6 |
| D5 | 7.8 | 8.8 | 1.00 | 0.06 | 4.4 | 5.8 |
| D6 | 8.2 | 10.6 | 1.00 | 0.03 | 4.6 | 6.0 |

### Every checklist item (runs in which it was present)

| Item | Kind | What | Plain | Factory |
| --- | --- | --- | --- | --- |
| D1-01 | state | A name-check result that tells the customer the account is in a different or similar name  | 5/5 | 5/5 |
| D1-02 | state | A distinct state for a name that does not match at all (no match), with a warning | 1/5 | 3/5 |
| D1-03 | state | A state for when the name could not be checked (check unavailable) | 2/5 | 5/5 |
| D1-04 | state | A review screen before sending that repeats payee, account details, amount and reference t | 4/5 | 5/5 |
| D1-05 | state | A step where the customer approves the payment or confirms it is them (passcode, biometric | 5/5 | 5/5 |
| D1-06 | state | A result screen for the payment being sent that includes the amount and the payee | 5/5 | 5/5 |
| D1-07 | state | A state for an amount over the £1,000 new-payee limit or over the available balance, sayin | 3/5 | 4/5 |
| D1-08 | state | A state for the payment failing, being declined, or its outcome being unknown (for example | 1/5 | 5/5 |
| D1-09 | state | Input validation errors on the payee or amount form that say how to fix the problem | 2/5 | 5/5 |
| D1-10 | info | A scam or fraud warning relevant to paying someone new (for example checking the payee is  | 4/5 | 5/5 |
| D1-11 | info | When the payment will arrive (for example 'usually within 2 hours' or 'within minutes') | 5/5 | 5/5 |
| D1-12 | info | A way to get help from the bank or to stop and contact the bank during the journey | 2/5 | 5/5 |
| D2-01 | info | A summary box (a table or list of standard questions about the account, including 'What is | 0/5 | 5/5 |
| D2-02 | info | An explanation of what AER means, or of the difference between AER and gross | 0/5 | 3/5 |
| D2-03 | info | A statement that the rate is variable and can change (beyond the single word 'variable' in | 4/5 | 5/5 |
| D2-04 | info | FSCS deposit protection mentioned with a limit | 0/5 | 5/5 |
| D2-05 | info | A way to get help from a person during the journey (a help link, chat or phone) | 1/5 | 5/5 |
| D2-06 | info | An example of interest in pounds (for example the balance after 12 months on £1,000, or in | 0/5 | 2/5 |
| D2-07 | info | The right to change her mind or cancel within 14 days | 0/5 | 3/5 |
| D2-08 | state | A step where the customer explicitly agrees to terms that are available to read (not pre-t | 0/5 | 2/5 |
| D2-09 | state | A review screen before opening that repeats the account, the amount and where the money co | 5/5 | 5/5 |
| D2-10 | state | A result screen showing the account is open with £500.00 in it and what happens next (for  | 5/5 | 5/5 |
| D2-11 | state | Validation of the opening amount (below £1, above the available balance or above the maxim | 5/5 | 5/5 |
| D2-12 | state | A state for the opening or the transfer failing, saying what happened to the money | 3/5 | 5/5 |
| D3-01 | info | A plain statement that an overdraft is borrowing or a form of credit (debt), or that it is | 3/5 | 5/5 |
| D3-02 | info | The APR described as 'representative' | 0/5 | 0/5 |
| D3-03 | info | The cost shown in pounds for an example (an amount borrowed for a number of days), or a co | 4/5 | 5/5 |
| D3-04 | info | A statement about the effect on her credit file or score (an eligibility check that does n | 4/5 | 5/5 |
| D3-05 | state | The lower offer of £350 presented clearly as less than the £500 asked for, with accepting  | 4/5 | 5/5 |
| D3-06 | state | A declined state that is its own screen | 5/5 | 5/5 |
| D3-07 | info | On being declined: that credit reference agency information was used, or that she can ask  | 0/5 | 5/5 |
| D3-08 | info | Help for money worries: the bank's support and/or free independent debt advice (for exampl | 5/5 | 5/5 |
| D3-09 | info | The right to withdraw within 14 days, or how to reduce or remove the overdraft later | 2/5 | 5/5 |
| D3-10 | state | A step where she explicitly agrees to the overdraft agreement, with the agreement or pre-c | 0/5 | 5/5 |
| D3-11 | info | Why income and outgoings are asked for (affordability) | 4/5 | 5/5 |
| D3-12 | state | A result screen for the accepted overdraft stating the limit, the rate and when it is avai | 3/5 | 5/5 |
| D4-01 | state | A way to freeze the card temporarily (reversible), separate from cancelling it | 5/5 | 5/5 |
| D4-02 | state | The frozen state shown in words, with a way to unfreeze | 5/5 | 4/5 |
| D4-03 | state | A question or choice that separates lost from stolen (or 'someone has used it') | 3/5 | 2/5 |
| D4-04 | info | A statement before confirming that cancelling the card is permanent or cannot be undone | 3/5 | 4/5 |
| D4-05 | state | A way to mark the NVX*DIGITAL payment as not recognised and report it | 5/5 | 5/5 |
| D4-06 | info | What happens next with the unrecognised payment (the bank will look into it or refund it,  | 1/5 | 0/5 |
| D4-07 | state | Confirmation of the delivery address for the replacement, with a way to say it is wrong | 5/5 | 4/5 |
| D4-08 | info | What still works or stops working while the card is frozen or cancelled (for example Direc | 5/5 | 5/5 |
| D4-09 | state | A result screen stating the card is cancelled and the replacement arrives in 3 to 5 workin | 4/5 | 5/5 |
| D4-10 | info | A phone number or other route to a person (for example the fraud team) in the journey | 1/5 | 4/5 |
| D4-11 | info | Security reassurance or advice (for example the bank will never ask for her PIN, or what t | 0/5 | 5/5 |
| D4-12 | state | A state for the freeze, cancellation or order failing, saying what to do (for example call | 0/5 | 4/5 |
| D5-01 | state | A summary in words of total spending and the comparison with October (about £96 less) | 5/5 | 5/5 |
| D5-02 | state | Every category's amount shown as text next to or in its chart mark (not only in a legend o | 5/5 | 5/5 |
| D5-03 | state | The comparison says it is like for like (same point in last month), not the whole of Octob | 5/5 | 5/5 |
| D5-04 | state | The groceries budget shows spent (£212.35), the budget (£300.00) and what is left (£87.65) | 4/5 | 5/5 |
| D5-05 | state | The budget relates the money left to the time left in the month (for example 12 days left) | 0/5 | 5/5 |
| D5-06 | state | A category detail screen listing the six groceries payments with dates | 5/5 | 5/5 |
| D5-07 | state | A way to set a budget for a category that has none | 4/5 | 2/5 |
| D5-08 | state | A way to change or remove the existing budget | 3/5 | 0/5 |
| D5-09 | state | An over-budget state shown in words | 0/5 | 0/5 |
| D5-10 | state | An empty or loading state (for example a month or category with no spending, or data unava | 0/5 | 4/5 |
| D5-11 | state | A way to correct a payment's category, or to see how categories are decided | 3/5 | 3/5 |
| D5-12 | state | Pending or incomplete data acknowledged (for example 'so far', 'up to 18 November', or pen | 5/5 | 5/5 |
| D6-01 | state | The Everyday balance labelled as 'available' balance (or the kind of balance stated) | 5/5 | 5/5 |
| D6-02 | state | The Tesco Express payment marked 'Pending' in words | 5/5 | 5/5 |
| D6-03 | state | An explanation of what pending means, on the home or the payment detail | 5/5 | 5/5 |
| D6-04 | state | The upcoming payments with a total (£1,099.50) or what will be left after them | 4/5 | 5/5 |
| D6-05 | state | Money in distinguished from money out by more than colour (a plus sign or words) | 5/5 | 5/5 |
| D6-06 | state | A payment detail screen with date, amount, payment method or type, and status | 4/5 | 3/5 |
| D6-07 | state | From the payment detail: a way to report a problem with the payment or get help | 4/5 | 5/5 |
| D6-08 | state | A loading state for the home screen | 0/5 | 5/5 |
| D6-09 | state | A state for balances or payments being unavailable (an error state that does not show £0.0 | 0/5 | 5/5 |
| D6-10 | state | A way to hide balances | 0/5 | 1/5 |
| D6-11 | state | Payments grouped or labelled by day with dates | 5/5 | 5/5 |
| D6-12 | state | Quick actions (for example pay, move money, card, help) with text labels | 4/5 | 4/5 |

### axe rules violated (number of runs with at least one violation)

| Rule | Plain | Factory |
| --- | --- | --- |
| aria-prohibited-attr | 2 | 4 |
| color-contrast | 27 | 1 |
| definition-list | 0 | 1 |
| dlitem | 0 | 4 |
| target-size | 1 | 1 |

## Cost and process

Tokens and seconds are means per run (lower is cheaper). Cost at gpt-5.6-luna list prices.

| Arm | Runs | Input tokens | of which cached | Output tokens | Seconds | Cost per run | Design files written | research.md words | Distinct URLs in research.md | Runs whose final message mentions accessibility, WCAG or compliance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Plain | 30 | 192k | 167k | 9.7k | 192 | $0.020 | 0.0 | 830 | 7.5 | 4 |
| Factory | 30 | 1321k | 1251k | 22.0k | 435 | $0.065 | 5.5 | 521 | 4.4 | 3 |

FSCS limit shown in D2 storyboards (the limit has been £120,000 since 1 December 2025): plain: £85,000 in 0, £120,000 in 0, none in 5; factory: £85,000 in 0, £120,000 in 5, none in 0 runs.

