Regraded 40 replies with no final message; now right: 36.

| model | benchmark | variant | right after regrading |
| --- | --- | --- | --- |
| local | gsm8k | orig | 177/184 |
| local | gsm8k | numbers | 172/184 |
| local | gsm8k | names | 63/64 |
| local | gsm8k | both | 60/64 |
| local | humaneval | orig | 78/80 |
| local | humaneval | renamed | 78/80 |
| hosted | gsm8k | orig | 175/184 |
| hosted | gsm8k | numbers | 172/184 |
| hosted | gsm8k | names | 63/64 |
| hosted | gsm8k | both | 60/64 |
| hosted | humaneval | orig | 75/80 |
| hosted | humaneval | renamed | 75/80 |

| comparison | orig right only / same / twin right only | mean effect | p (unadjusted) |
| --- | --- | --- | --- |
| H1 local, GSM8K numbers | 6 / 177 / 1 | +2.7 pts | 0.0625 |
| H2 local, GSM8K names | 0 / 64 / 0 | +0.0 pts | 1.0000 |
| H3 local, HumanEval renamed | 1 / 78 / 1 | +0.0 pts | 0.7500 |
| H4 numbers drop, local vs hosted | 4 / 178 / 2 | +1.1 pts | 0.6875 |
