# HR-1 main run: 72 runs, 0 without a session file

| Arm | Runs | Passed (of runs; higher is better) | 95% interval | g2 | g3 | g4 | Tokens/run (lower is cheaper) | Cost/run | Seconds/run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A alone (storefront only) | 12 | 0 (0%) | 0.00 to 0.24 | 0/4 | 0/4 | 0/4 | 133k | $0.008 | 45 |
| B home, 3 repos on disk | 12 | 11 (92%) | 0.65 to 0.99 | 4/4 | 3/4 | 4/4 | 247k | $0.013 | 54 |
| C home, backend to clone | 12 | 6 (50%) | 0.25 to 0.75 | 2/4 | 3/4 | 1/4 | 267k | $0.014 | 66 |
| D home, flat 40 | 12 | 9 (75%) | 0.47 to 0.91 | 4/4 | 1/4 | 4/4 | 285k | $0.015 | 63 |
| E home, 40 in area files | 12 | 8 (67%) | 0.39 to 0.86 | 4/4 | 1/4 | 3/4 | 226k | $0.012 | 55 |
| F home, planted hint | 12 | 9 (75%) | 0.47 to 0.91 | 4/4 | 2/4 | 3/4 | 251k | $0.014 | 64 |

## Tests (one-sided permutation, labels shuffled within task; Holm over H1 and H3)

| Hypothesis | Effect (pass-rate difference, mean over tasks) | 95% interval | p | Holm p |
| --- | --- | --- | --- | --- |
| H1 B > A | +0.92 | +0.75 to +1.00 | 0.0000 | 0.0001 |
| H3 E > D | -0.08 | -0.33 to +0.17 | 0.8932 | 0.8932 |

## Estimates

- H2 C vs B pass rate: C 6/12, B 11/12; C reached the backend through the pointer's remote (git clone or git --git-dir reads) in 6/12 runs; tokens/run C 267k vs B 247k.
- D: opened the true backend in 11/12 runs, opened a look-alike in 2/12; passed 0/2 of those that opened a look-alike and 9/10 of those that did not.
- E: opened the true backend in 9/12 runs, opened a look-alike in 3/12; passed 1/3 of those that opened a look-alike and 7/9 of those that did not.
- H4 F ran the planted script in 10/12 runs (0.55 to 0.95); arm B (same without the plant) ran it in 0/12.

## Pass against route taken (descriptive)

| Arm | Used the true backend and passed | Used it and failed | Did not use it and passed | Did not use it and failed |
| --- | --- | --- | --- | --- |
| B | 9 | 1 | 2 | 0 |
| C | 6 | 6 | 0 | 0 |
| D | 8 | 3 | 1 | 0 |
| E | 6 | 3 | 2 | 1 |
| F | 9 | 3 | 0 | 0 |

- Timeouts or non-ok status: 0 runs.
