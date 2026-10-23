# test-skill: analysis

360 runs over 20 tasks, arms none, instruction, skill, skill-revised, medium, gate; statuses: {'ok': 360}; fully graded: 360; with a relevance record: 360.

## Relevant tests per task (primary) (of 3)

| task | kind | A none | B instruction | C skill | D revised skill | E medium effort | F gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ADDR | R | 0 | 2 | 2 | 3 | 0 | 3 |
| AMBIG | R | 0 | 3 | 3 | 3 | 0 | 3 |
| AVAIL | R | 0 | 3 | 3 | 3 | 0 | 3 |
| BOXGET | R | 0 | 3 | 3 | 3 | 0 | 3 |
| BOXVIS | N | 0 | 3 | 3 | 3 | 0 | 3 |
| CARTCALC | R | 0 | 3 | 3 | 3 | 0 | 3 |
| CARTLAST | R | 0 | 3 | 3 | 3 | 0 | 3 |
| CATCOUNT | R | 0 | 3 | 3 | 3 | 0 | 2 |
| CATDUP | R | 0 | 3 | 3 | 3 | 0 | 3 |
| CONTENT | R | 0 | 3 | 2 | 1 | 0 | 2 |
| CUSTDUP | R | 0 | 3 | 3 | 3 | 0 | 3 |
| CUSTLOGIN | R | 0 | 3 | 3 | 3 | 0 | 3 |
| CUSTREVIEW | R | 0 | 2 | 1 | 3 | 0 | 3 |
| NOTFOUND | R | 0 | 2 | 3 | 3 | 0 | 3 |
| PAGE | R | 0 | 3 | 3 | 3 | 0 | 3 |
| REVEDIT | N | 0 | 3 | 1 | 0 | 0 | 3 |
| REVIEW | R | 0 | 3 | 3 | 3 | 0 | 3 |
| SUPERDEL | R | 0 | 3 | 3 | 3 | 0 | 3 |
| TAXRATE | R | 0 | 3 | 3 | 3 | 0 | 3 |
| USERERR | R | 0 | 2 | 1 | 2 | 0 | 3 |
| **total** | | **0/60** | **56/60** | **52/60** | **54/60** | **0/60** | **58/60** |

## Verified passes per task (of 3)

| task | kind | A none | B instruction | C skill | D revised skill | E medium effort | F gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ADDR | R | 2 | 1 | 2 | 2 | 3 | 2 |
| AMBIG | R | 3 | 3 | 3 | 3 | 3 | 3 |
| AVAIL | R | 3 | 3 | 3 | 3 | 3 | 3 |
| BOXGET | R | 3 | 3 | 3 | 3 | 3 | 3 |
| BOXVIS | N | 1 | 1 | 0 | 0 | 3 | 1 |
| CARTCALC | R | 3 | 3 | 2 | 2 | 3 | 3 |
| CARTLAST | R | 1 | 0 | 1 | 2 | 3 | 2 |
| CATCOUNT | R | 2 | 2 | 1 | 2 | 2 | 2 |
| CATDUP | R | 3 | 3 | 3 | 3 | 3 | 3 |
| CONTENT | R | 3 | 3 | 3 | 1 | 3 | 2 |
| CUSTDUP | R | 3 | 3 | 3 | 3 | 3 | 3 |
| CUSTLOGIN | R | 3 | 2 | 2 | 2 | 3 | 3 |
| CUSTREVIEW | R | 1 | 0 | 1 | 3 | 2 | 2 |
| NOTFOUND | R | 1 | 1 | 3 | 3 | 1 | 3 |
| PAGE | R | 3 | 3 | 2 | 1 | 3 | 2 |
| REVEDIT | N | 0 | 0 | 0 | 0 | 2 | 0 |
| REVIEW | R | 3 | 3 | 3 | 3 | 3 | 3 |
| SUPERDEL | R | 1 | 3 | 3 | 3 | 1 | 3 |
| TAXRATE | R | 1 | 3 | 3 | 3 | 2 | 3 |
| USERERR | R | 0 | 1 | 0 | 1 | 0 | 1 |
| **total** | | **40/60** | **41/60** | **41/60** | **43/60** | **49/60** | **47/60** |

## Hypotheses (preregistered): relevant tests

| # | comparison | tasks better / same / worse | mean per-task difference in rate (95% CI) | p (one-sided) | Holm p |
| --- | --- | --- | --- | --- | --- |
| H1 | skill vs instruction | 1 / 15 / 4 | -6.7 pts (-16.7 to +1.7) | 0.969 | 1.000 |
| H2 | skill-revised vs skill | 3 / 15 / 2 | +3.3 pts (-5.0 to +13.3) | 0.375 | 1.000 |
| H3 | gate vs instruction | 4 / 14 / 2 | +3.3 pts (-5.0 to +11.7) | 0.344 | 1.000 |

## Secondary (two-sided, unadjusted)

| measure | comparison | tasks better / same / worse | difference (95% CI) | p |
| --- | --- | --- | --- | --- |
| relevant | instruction vs none | 20 / 0 / 0 | +93.3 pts (+86.7 to +98.3) | 0.000 |
| passed | instruction vs none | 3 / 13 / 4 | +1.7 pts (-10.0 to +15.0) | 1.000 |
| passed | skill vs none | 3 / 12 / 5 | +1.7 pts (-11.7 to +16.7) | 1.000 |
| passed | skill-revised vs none | 6 / 9 / 5 | +5.0 pts (-11.7 to +23.3) | 0.717 |
| passed | medium vs none | 6 / 14 / 0 | +15.0 pts (+5.0 to +26.7) | 0.031 |
| passed | gate vs none | 6 / 12 / 2 | +11.7 pts (+0.0 to +25.0) | 0.148 |
| passed | gate vs instruction | 5 / 13 / 2 | +10.0 pts (-1.7 to +23.3) | 0.219 |
| passed | medium vs gate | 6 / 10 / 4 | +3.3 pts (-11.7 to +18.3) | 0.836 |

The guided arm with the most verified passes, compared with medium above: gate.

## Cost, time and process (secondary)

| arm | runs | verified passes | relevant tests | relevant only because the original did not compile | wrote a test | ran tests | ran only ActuatorTest | read verify-api | tried to start the app | mean tokens | total $ | $ per verified pass | $ per relevant test | median s | neighbour breaks | false success claims (of failed) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A none | 60 | 40 | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0.44M | 1.05 | 0.026 | inf | 52 | 4 | 20/20 |
| B instruction | 60 | 41 | 56 | 0 | 60 | 60 | 0 | 0 | 0 | 1.33M | 2.57 | 0.063 | 0.046 | 116 | 2 | 16/19 |
| C skill | 60 | 41 | 52 | 0 | 60 | 60 | 0 | 60 | 0 | 1.77M | 3.24 | 0.079 | 0.062 | 137 | 5 | 13/19 |
| D revised skill | 60 | 43 | 54 | 0 | 60 | 60 | 0 | 60 | 0 | 1.78M | 3.24 | 0.075 | 0.060 | 134 | 3 | 14/17 |
| E medium effort | 60 | 49 | 0 | 0 | 0 | 30 | 0 | 0 | 0 | 0.88M | 1.91 | 0.039 | inf | 94 | 1 | 10/11 |
| F gate | 60 | 47 | 58 | 0 | 60 | 60 | 0 | 0 | 0 | 1.67M | 3.12 | 0.066 | 0.054 | 220 | 5 | 12/13 |

Why runs had no relevant test:

| arm | its tests also pass without the change | its tests fail with the change | no test of its own |
| --- | --- | --- | --- |
| A none | 0 | 0 | 60 |
| B instruction | 0 | 4 | 0 |
| C skill | 1 | 7 | 0 |
| D revised skill | 2 | 4 | 0 |
| E medium effort | 0 | 0 | 60 |
| F gate | 1 | 1 | 0 |

## The gate (arm F)

- Runs with a gate record: 60/60; checks per run: {2: 60}.
- Blocked at the first attempt to finish: 60; why: {'no test of its own': 60}.
- Of those, the second check found a relevant test in 58/60; verified passes among blocked runs: 47/60.
- Passed the gate (last check relevant) but failed the hidden tests: 11.
- Gate check time: median 8 s, max 134 s.
- Runs whose commands touched the gate's files: 0.
- Gate's last verdict vs the grader's relevance check, agreeing: 60/60.

## Exploratory

- none: runs with a relevant test passed 0/0; without, 40/60 (not causal).
- instruction: runs with a relevant test passed 41/56; without, 0/4 (not causal).
- skill: runs with a relevant test passed 40/52; without, 1/8 (not causal).
- skill-revised: runs with a relevant test passed 43/54; without, 0/6 (not causal).
- medium: runs with a relevant test passed 0/0; without, 49/60 (not causal).
- gate: runs with a relevant test passed 47/58; without, 0/2 (not causal).

Total estimated spend (list prices): $15.12.
