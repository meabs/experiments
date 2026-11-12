# Exploratory re-score: cropped to the screen interior

Same pairs, same judges, same prompt; only the images differ. Score per pair = share of the judge votes (two judges, two orders) that chose the factory's design; above 0.5 the factory wins the pair, below 0.5 the plain agent does. Not a pre-registered test.

| View | Images | Pairs | Factory wins | Plain wins | Split | Mean score (95% CI) | p (sign-flip) | Sign test p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| whole design | original screenshots | 30 | 14 | 11 | 5 | 0.53 (0.39 to 0.66) | 0.8015 | 0.6900 |
| whole design | cropped to the screen | 30 | 11 | 17 | 2 | 0.38 (0.25 to 0.53) | 0.1464 | 0.3449 |
| looks only (first six screens) | original screenshots | 30 | 6 | 21 | 3 | 0.32 (0.19 to 0.45) | 0.0154 | 0.0059 |
| looks only (first six screens) | cropped to the screen | 30 | 6 | 19 | 5 | 0.32 (0.21 to 0.43) | 0.0087 | 0.0146 |

### By criterion (mean pair score; above 0.5 favours the factory)

| Criterion | Whole: original | Whole: cropped | Looks: original | Looks: cropped |
| --- | --- | --- | --- | --- |
| overall | 0.53 | 0.38 | 0.32 | 0.32 |
| hierarchy | 0.40 | 0.25 | 0.32 | 0.30 |
| polish | 0.44 | 0.24 | 0.37 | 0.27 |
| identity | 0.13 | 0.12 | 0.14 | 0.15 |
| content | 0.66 | 0.62 | 0.50 | 0.51 |
| trust | 0.72 | 0.57 | 0.51 | 0.50 |
| journey | 0.72 | 0.65 | - | - |

### The judges

Chose the first design shown (50% = no position bias); same choice in both orders.

| Images | Judge | Calls | Chose first design shown | Same choice in both orders |
| --- | --- | --- | --- | --- |
| original screenshots | google/gemini-4-argon | 120 | 68% | 63% |
| original screenshots | anthropic/claude-sonnet-5.5 | 120 | 51% | 82% |
| cropped to the screen | google/gemini-4-argon | 120 | 70% | 60% |
| cropped to the screen | anthropic/claude-sonnet-5.5 | 120 | 45% | 87% |
