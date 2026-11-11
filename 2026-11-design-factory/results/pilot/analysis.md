# Analysis: pilot

8 runs, 2 pairs (plain run i with factory run i of the same brief). A = plain agent, B = Design Factory.

## Which design do the judges prefer?

Each pair gets a score from 0 to 1: the share of its judge votes (two judges, two orders) that chose the factory's design; a tie counts half. Above 0.5 the factory wins the pair, below 0.5 the plain agent does. 0.5 overall means no preference. p is a two-sided sign-flip permutation test on the pair scores; the sign test counts wins only.

| Question | Pairs | Factory wins | Plain wins | Split | Mean score (95% CI) | p | Holm p | Sign test p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 whole design | 2 | 1 | 0 | 1 | 0.75 (0.50 to 1.00) | 1.0000 | 1.0000 | 1.0000 |
| H2 looks only (first six screens) | 2 | 0 | 1 | 1 | 0.38 (0.25 to 0.50) | 1.0000 | 1.0000 | 1.0000 |

### By criterion (mean pair score; above 0.5 favours the factory; descriptive)

| Criterion | Whole design | Looks only |
| --- | --- | --- |
| overall | 0.75 | 0.38 |
| hierarchy | 0.50 | 0.25 |
| polish | 0.38 | 0.25 |
| identity | 0.50 | 0.50 |
| content | 0.88 | 0.75 |
| trust | 0.88 | 0.62 |
| journey | 0.88 | - |

### By brief (mean pair score; factory wins-plain wins-split)

| Brief | Whole: score | Whole: W-L-S | Looks: score | Looks: W-L-S |
| --- | --- | --- | --- | --- |
| D1 | 1.00 | 1-0-0 | 0.50 | 0-0-1 |
| D2 | - | 0-0-0 | - | 0-0-0 |
| D3 | - | 0-0-0 | - | 0-0-0 |
| D4 | - | 0-0-0 | - | 0-0-0 |
| D5 | 0.50 | 0-0-1 | 0.25 | 0-1-0 |
| D6 | - | 0-0-0 | - | 0-0-0 |

### The judges

Chose the first design shown: 50% means no position bias. Same choice in both orders: how often a judge picked the same design whichever came first (a pair where it flips counts as a split).

| Judge | Calls | Chose the design shown first | Same choice in both orders | Mean vote for factory |
| --- | --- | --- | --- | --- |
| google/gemini-4-argon | 8 | 88% | 25% | 0.62 |
| anthropic/claude-sonnet-5.5 | 8 | 25% | 50% | 0.50 |

The two judges reached the same pair result (factory, plain or split) in 75% of 4 pair-views.

## Checklist, accessibility checks

Checklist: share of the brief's 12 checklist items visible in the prototype's text (higher is better). axe: WCAG A and AA rule violations found by axe-core per screen (lower is better). Difference = factory minus plain, per pair.

| Measure | Pairs | Plain | Factory | Difference (95% CI) | p | Holm p |
| --- | --- | --- | --- | --- | --- | --- |
| H3 checklist items present (share of 12) | 2 | 0.40 | 0.88 | +0.33 (+0.17 to +0.50) | 0.5000 | 1.0000 |
| H4 axe rule violations per screen (lower is better) | 2 | 0.34 | 0.00 | -0.45 (-0.90 to +0.00) | 1.0000 | 1.0000 |

### Descriptive measures (means over runs; no tests)

| Measure | Plain | Factory |
| --- | --- | --- |
| Checklist: 'state' items present | 47% | 86% |
| Checklist: 'info' items present | 23% | 100% |
| Screens delivered | 6.0 | 10.5 |
| Delivery contract met (screens.json and every screen opens) | 100% | 100% |
| Screens with no axe violation | 66% | 100% |
| Screens that scroll sideways at 320 px (lower is better) | 17% | 0% |
| Controls at least 24 px in both directions | 82% | 87% |
| Controls at least 44 px in both directions | 41% | 78% |
| Screens with exactly one h1 | 93% | 100% |
| Clickable things not reachable by keyboard, per run (lower is better) | 0.2 | 0.0 |
| Console errors per run (lower is better) | 0.0 | 21.0 |

### By brief

| Brief | Checklist of 12: plain | factory | axe per screen: plain | factory | Screens: plain | factory |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | 5.0 | 11.0 | 0.90 | 0.00 | 10.0 | 13.0 |
| D2 | 3.0 | nan | 0.17 | nan | 6.0 | nan |
| D3 | 4.0 | nan | 0.29 | nan | 7.0 | nan |
| D4 | 3.0 | nan | 0.17 | nan | 6.0 | nan |
| D5 | 8.0 | 10.0 | 0.00 | 0.00 | 5.0 | 8.0 |
| D6 | 6.0 | nan | 0.50 | nan | 2.0 | nan |

### Every checklist item (runs in which it was present)

| Item | Kind | What | Plain | Factory |
| --- | --- | --- | --- | --- |
| D1-01 | state | A name-check result that tells the customer the account is in a different or similar name  | 1/1 | 1/1 |
| D1-02 | state | A distinct state for a name that does not match at all (no match), with a warning | 0/1 | 0/1 |
| D1-03 | state | A state for when the name could not be checked (check unavailable) | 0/1 | 1/1 |
| D1-04 | state | A review screen before sending that repeats payee, account details, amount and reference t | 1/1 | 1/1 |
| D1-05 | state | A step where the customer approves the payment or confirms it is them (passcode, biometric | 1/1 | 1/1 |
| D1-06 | state | A result screen for the payment being sent that includes the amount and the payee | 1/1 | 1/1 |
| D1-07 | state | A state for an amount over the £1,000 new-payee limit or over the available balance, sayin | 0/1 | 1/1 |
| D1-08 | state | A state for the payment failing, being declined, or its outcome being unknown (for example | 0/1 | 1/1 |
| D1-09 | state | Input validation errors on the payee or amount form that say how to fix the problem | 0/1 | 1/1 |
| D1-10 | info | A scam or fraud warning relevant to paying someone new (for example checking the payee is  | 0/1 | 1/1 |
| D1-11 | info | When the payment will arrive (for example 'usually within 2 hours' or 'within minutes') | 1/1 | 1/1 |
| D1-12 | info | A way to get help from the bank or to stop and contact the bank during the journey | 0/1 | 1/1 |
| D2-01 | info | A summary box (a table or list of standard questions about the account, including 'What is | 0/1 | 0/0 |
| D2-02 | info | An explanation of what AER means, or of the difference between AER and gross | 0/1 | 0/0 |
| D2-03 | info | A statement that the rate is variable and can change (beyond the single word 'variable' in | 1/1 | 0/0 |
| D2-04 | info | FSCS deposit protection mentioned with a limit | 0/1 | 0/0 |
| D2-05 | info | A way to get help from a person during the journey (a help link, chat or phone) | 0/1 | 0/0 |
| D2-06 | info | An example of interest in pounds (for example the balance after 12 months on £1,000, or in | 0/1 | 0/0 |
| D2-07 | info | The right to change her mind or cancel within 14 days | 0/1 | 0/0 |
| D2-08 | state | A step where the customer explicitly agrees to terms that are available to read (not pre-t | 0/1 | 0/0 |
| D2-09 | state | A review screen before opening that repeats the account, the amount and where the money co | 1/1 | 0/0 |
| D2-10 | state | A result screen showing the account is open with £500.00 in it and what happens next (for  | 1/1 | 0/0 |
| D2-11 | state | Validation of the opening amount (below £1, above the available balance or above the maxim | 0/1 | 0/0 |
| D2-12 | state | A state for the opening or the transfer failing, saying what happened to the money | 0/1 | 0/0 |
| D3-01 | info | A plain statement that an overdraft is borrowing or a form of credit (debt), or that it is | 0/1 | 0/0 |
| D3-02 | info | The APR described as 'representative' | 0/1 | 0/0 |
| D3-03 | info | The cost shown in pounds for an example (an amount borrowed for a number of days), or a co | 0/1 | 0/0 |
| D3-04 | info | A statement about the effect on her credit file or score (an eligibility check that does n | 1/1 | 0/0 |
| D3-05 | state | The lower offer of £350 presented clearly as less than the £500 asked for, with accepting  | 0/1 | 0/0 |
| D3-06 | state | A declined state that is its own screen | 1/1 | 0/0 |
| D3-07 | info | On being declined: that credit reference agency information was used, or that she can ask  | 0/1 | 0/0 |
| D3-08 | info | Help for money worries: the bank's support and/or free independent debt advice (for exampl | 0/1 | 0/0 |
| D3-09 | info | The right to withdraw within 14 days, or how to reduce or remove the overdraft later | 0/1 | 0/0 |
| D3-10 | state | A step where she explicitly agrees to the overdraft agreement, with the agreement or pre-c | 0/1 | 0/0 |
| D3-11 | info | Why income and outgoings are asked for (affordability) | 1/1 | 0/0 |
| D3-12 | state | A result screen for the accepted overdraft stating the limit, the rate and when it is avai | 1/1 | 0/0 |
| D4-01 | state | A way to freeze the card temporarily (reversible), separate from cancelling it | 0/1 | 0/0 |
| D4-02 | state | The frozen state shown in words, with a way to unfreeze | 0/1 | 0/0 |
| D4-03 | state | A question or choice that separates lost from stolen (or 'someone has used it') | 0/1 | 0/0 |
| D4-04 | info | A statement before confirming that cancelling the card is permanent or cannot be undone | 0/1 | 0/0 |
| D4-05 | state | A way to mark the NVX*DIGITAL payment as not recognised and report it | 1/1 | 0/0 |
| D4-06 | info | What happens next with the unrecognised payment (the bank will look into it or refund it,  | 0/1 | 0/0 |
| D4-07 | state | Confirmation of the delivery address for the replacement, with a way to say it is wrong | 1/1 | 0/0 |
| D4-08 | info | What still works or stops working while the card is frozen or cancelled (for example Direc | 1/1 | 0/0 |
| D4-09 | state | A result screen stating the card is cancelled and the replacement arrives in 3 to 5 workin | 0/1 | 0/0 |
| D4-10 | info | A phone number or other route to a person (for example the fraud team) in the journey | 0/1 | 0/0 |
| D4-11 | info | Security reassurance or advice (for example the bank will never ask for her PIN, or what t | 0/1 | 0/0 |
| D4-12 | state | A state for the freeze, cancellation or order failing, saying what to do (for example call | 0/1 | 0/0 |
| D5-01 | state | A summary in words of total spending and the comparison with October (about £96 less) | 1/1 | 1/1 |
| D5-02 | state | Every category's amount shown as text next to or in its chart mark (not only in a legend o | 1/1 | 1/1 |
| D5-03 | state | The comparison says it is like for like (same point in last month), not the whole of Octob | 1/1 | 1/1 |
| D5-04 | state | The groceries budget shows spent (£212.35), the budget (£300.00) and what is left (£87.65) | 1/1 | 1/1 |
| D5-05 | state | The budget relates the money left to the time left in the month (for example 12 days left) | 1/1 | 1/1 |
| D5-06 | state | A category detail screen listing the six groceries payments with dates | 1/1 | 1/1 |
| D5-07 | state | A way to set a budget for a category that has none | 0/1 | 1/1 |
| D5-08 | state | A way to change or remove the existing budget | 1/1 | 0/1 |
| D5-09 | state | An over-budget state shown in words | 0/1 | 0/1 |
| D5-10 | state | An empty or loading state (for example a month or category with no spending, or data unava | 0/1 | 1/1 |
| D5-11 | state | A way to correct a payment's category, or to see how categories are decided | 0/1 | 1/1 |
| D5-12 | state | Pending or incomplete data acknowledged (for example 'so far', 'up to 18 November', or pen | 1/1 | 1/1 |
| D6-01 | state | The Everyday balance labelled as 'available' balance (or the kind of balance stated) | 0/1 | 0/0 |
| D6-02 | state | The Tesco Express payment marked 'Pending' in words | 1/1 | 0/0 |
| D6-03 | state | An explanation of what pending means, on the home or the payment detail | 1/1 | 0/0 |
| D6-04 | state | The upcoming payments with a total (£1,099.50) or what will be left after them | 0/1 | 0/0 |
| D6-05 | state | Money in distinguished from money out by more than colour (a plus sign or words) | 1/1 | 0/0 |
| D6-06 | state | A payment detail screen with date, amount, payment method or type, and status | 1/1 | 0/0 |
| D6-07 | state | From the payment detail: a way to report a problem with the payment or get help | 1/1 | 0/0 |
| D6-08 | state | A loading state for the home screen | 0/1 | 0/0 |
| D6-09 | state | A state for balances or payments being unavailable (an error state that does not show £0.0 | 0/1 | 0/0 |
| D6-10 | state | A way to hide balances | 0/1 | 0/0 |
| D6-11 | state | Payments grouped or labelled by day with dates | 1/1 | 0/0 |
| D6-12 | state | Quick actions (for example pay, move money, card, help) with text labels | 0/1 | 0/0 |

### axe rules violated (number of runs with at least one violation)

| Rule | Plain | Factory |
| --- | --- | --- |
| color-contrast | 5 | 0 |

## Cost and process

Tokens and seconds are means per run (lower is cheaper). Cost at gpt-5.6-luna list prices.

| Arm | Runs | Input tokens | of which cached | Output tokens | Seconds | Cost per run | Design files written | Runs whose final message mentions accessibility, WCAG or compliance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Plain | 6 | 87k | 67k | 6.6k | 131 | $0.013 | 0.0 | 0 |
| Factory | 2 | 565k | 519k | 17.7k | 338 | $0.041 | 6.0 | 0 |

FSCS limit shown in D2 prototypes (the limit has been £120,000 since 1 December 2025): plain: £85,000 in 0, £120,000 in 0, none in 1; factory: £85,000 in 0, £120,000 in 0, none in 0 runs.

