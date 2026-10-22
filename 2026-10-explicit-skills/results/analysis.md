# explicit-skills: analysis

240 runs over 20 tasks; statuses: {'ok': 240}.

## Passes per task (of 3)

| task | kind | A none | B discover | C explicit | D AGENTS.md entry |
| --- | --- | --- | --- | --- | --- |
| ADDR | R | 3 | 3 | 3 | 3 |
| AMBIG | R | 3 | 3 | 3 | 3 |
| AVAIL | R | 3 | 2 | 3 | 3 |
| BOXGET | R | 3 | 3 | 3 | 3 |
| BOXVIS | N | 0 | 0 | 1 | 1 |
| CARTCALC | R | 3 | 3 | 3 | 3 |
| CARTLAST | R | 1 | 1 | 1 | 0 |
| CATCOUNT | R | 1 | 2 | 1 | 1 |
| CATDUP | R | 3 | 3 | 3 | 3 |
| CONTENT | R | 2 | 3 | 3 | 3 |
| CUSTDUP | R | 3 | 3 | 2 | 3 |
| CUSTLOGIN | R | 3 | 3 | 3 | 3 |
| CUSTREVIEW | R | 2 | 0 | 0 | 0 |
| NOTFOUND | R | 0 | 1 | 1 | 2 |
| PAGE | R | 3 | 3 | 3 | 3 |
| REVEDIT | N | 0 | 0 | 0 | 0 |
| REVIEW | R | 3 | 3 | 3 | 3 |
| SUPERDEL | R | 1 | 1 | 3 | 3 |
| TAXRATE | R | 0 | 2 | 3 | 3 |
| USERERR | R | 0 | 0 | 0 | 0 |
| **total** | | **37/60** | **39/60** | **42/60** | **43/60** |

## Hypotheses (preregistered)

| # | comparison | tasks better / same / worse | mean per-task difference in pass rate (95% CI) | p (one-sided) | Holm p |
| --- | --- | --- | --- | --- | --- |
| H1 | explicit vs none | 5 / 13 / 2 | +8.3 pts (-5.0 to +23.3) | 0.203 | 0.406 |
| H2 | explicit vs discover | 4 / 14 / 2 | +5.0 pts (-3.3 to +15.0) | 0.266 | 0.406 |

Added by amendment before any analysis (Holm-adjusted as their own pair):

| # | comparison | tasks better / same / worse | mean per-task difference in pass rate (95% CI) | p (one-sided) | Holm p |
| --- | --- | --- | --- | --- | --- |
| H3 | agentsmd vs none | 5 / 13 / 2 | +10.0 pts (-5.0 to +26.7) | 0.164 | 0.328 |
| H4 | agentsmd vs discover | 5 / 13 / 2 | +6.7 pts (-3.3 to +16.7) | 0.180 | 0.328 |

Secondary (two-sided, unadjusted): explicit vs agentsmd, 1 / 17 / 2, -1.7 pts (-6.7 to +3.3), p = 1.000.

Secondary (two-sided, unadjusted): discover vs none, 4 / 14 / 2, +3.3 pts (-8.3 to +15.0), p = 0.781.

Neighbour breaks (2 neighbour-break tasks), runs with a failing keeps... test: none 4, discover 5, explicit 5, agentsmd 4.

## Cost, time and process (secondary)

| arm | runs | verified passes | mean tokens | total $ | $ per verified pass | median s | read safe-change | read build-test | read verify-api | ran Maven tests | wrote tests | API-level test written | tried to start the app | neighbour breaks | false success claims (of failed) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A none | 60 | 37 | 0.40M | 1.02 | 0.028 | 53 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 4 | 23/23 |
| B discover | 60 | 39 | 0.56M | 1.31 | 0.034 | 73 | 60 | 58 | 3 | 16 | 0 | 0 | 0 | 5 | 21/21 |
| C explicit | 60 | 42 | 1.10M | 2.29 | 0.054 | 113 | 60 | 60 | 60 | 60 | 16 | 15 | 0 | 5 | 18/18 |
| D AGENTS.md entry | 60 | 43 | 0.99M | 2.09 | 0.049 | 117 | 60 | 58 | 60 | 59 | 11 | 10 | 0 | 4 | 17/17 |

Cost per verified pass, discover over none: 1.22 (95% CI 0.97 to 1.52, resampling tasks).

Cost per verified pass, explicit over none: 1.98 (95% CI 1.54 to 2.41, resampling tasks).

Cost per verified pass, agentsmd over none: 1.77 (95% CI 1.34 to 2.24, resampling tasks).

## Exploratory

- discover runs that read verify-api: 0/3 passed; that did not: 39/57 (not causal).
- discover runs that wrote an API-level test: 0/0 passed; that did not: 39/60 (not causal).
- explicit runs that read verify-api: 42/60 passed; that did not: 0/0 (not causal).
- explicit runs that wrote an API-level test: 13/15 passed; that did not: 29/45 (not causal).
- agentsmd runs that read verify-api: 43/60 passed; that did not: 0/0 (not causal).
- agentsmd runs that wrote an API-level test: 9/10 passed; that did not: 34/50 (not causal).

| kind | tasks | A none | B discover | C explicit | D AGENTS.md entry |
| --- | --- | --- | --- | --- | --- |
| N | 2 | 0/6 | 0/6 | 1/6 | 1/6 |
| R | 18 | 37/54 | 39/54 | 41/54 | 42/54 |

Total estimated spend (list prices): $6.70.
