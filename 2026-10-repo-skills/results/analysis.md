# repo-skills: analysis

120 runs over 20 tasks; statuses: {'ok': 120}.

## Passes per task (of 3)

| task | kind | A none | B repo skills |
| --- | --- | --- | --- |
| ADDR | R | 3 | 2 |
| AMBIG | R | 3 | 3 |
| AVAIL | R | 3 | 3 |
| BOXGET | R | 3 | 3 |
| BOXVIS | N | 1 | 0 |
| CARTCALC | R | 3 | 3 |
| CARTLAST | R | 3 | 2 |
| CATCOUNT | R | 1 | 2 |
| CATDUP | R | 3 | 3 |
| CONTENT | R | 2 | 3 |
| CUSTDUP | R | 3 | 3 |
| CUSTLOGIN | R | 3 | 2 |
| CUSTREVIEW | R | 0 | 2 |
| NOTFOUND | R | 1 | 2 |
| PAGE | R | 3 | 2 |
| REVEDIT | N | 0 | 0 |
| REVIEW | R | 3 | 3 |
| SUPERDEL | R | 0 | 2 |
| TAXRATE | R | 0 | 0 |
| USERERR | R | 0 | 0 |
| **total** | | **38/60** | **40/60** |

## H1 (preregistered)

| hypothesis | tasks better / same / worse | mean per-task difference in pass rate (95% CI) | p (one-sided) |
| --- | --- | --- | --- |
| repo-skills beats none | 5 / 10 / 5 | +3.3 pts (-8.3 to +16.7) | 0.404 |

**Secondary: cost per verified pass**, repo-skills over none = 1.29 (95% CI 1.01 to 1.55, resampling tasks).

**Secondary: neighbour breaks** (2 neighbour-break tasks): runs with a failing keeps... test, none 2, repo-skills 5.

## Cost, time and process (secondary)

| arm | runs | verified passes | mean tokens | total $ | $ per verified pass | median s | ran Maven tests | wrote tests | API-level test written | tried to start the app | called the app | read a skill | neighbour breaks | false success claims (of failed) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A none | 60 | 38 | 0.38M | 0.97 | 0.026 | 43 | 5 | 0 | 0 | 0 | 0 | 0 | 2 | 22/22 |
| B repo skills | 60 | 40 | 0.55M | 1.32 | 0.033 | 61 | 26 | 2 | 2 | 0 | 0 | 60 | 5 | 20/20 |

## Exploratory

- repo-skills runs that wrote an API-level test: 2/2 passed; that did not: 38/58 (not causal: harder tasks may draw more checking).
- repo-skills runs that ran Maven tests: 19/26 passed; that did not: 21/34 (not causal: harder tasks may draw more checking).

| kind | tasks | A none | B repo skills |
| --- | --- | --- | --- |
| N | 2 | 1/6 | 0/6 |
| R | 18 | 37/54 | 40/54 |

Total estimated spend (list prices): $2.30.
