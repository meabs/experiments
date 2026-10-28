# okf-local: checks after the runs

Made after the runs, from each run's Codex session file and the power log; not part of the fixed analysis.

## Model and effort in the session files

- `no_okf`: 20 session files name `qwen3.8:27b` at `medium` effort.
- `okf`: 20 session files name `qwen3.8:27b` at `medium` effort.
- `source`: 20 session files name `qwen3.8:27b` at `medium` effort.

## Tokens, time, energy and the hosted-price equivalent, per run (mean over the arm's 20 runs)

Lower is better in every column. Cached input is input the model server had already processed in an earlier turn of the same run. Hosted-price equivalent: what the same tokens would cost at gpt-5.6-luna list prices ($0.2 per million uncached input, $0.02 cached, $1.2 output); the local runs cost only electricity.

| Arm | Input tokens | of which cached | Output tokens | Wall time, total for 20 runs | Energy per run, Wh | Electricity per run (£0.25/kWh) | Hosted-price equivalent per run |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `no_okf` | 522k | 504k | 7.9k | 2.8 h | 11.5 | £0.0029 | $0.023 |
| `okf` | 317k | 279k | 4.4k | 2.0 h | 8.4 | £0.0021 | $0.018 |
| `source` | 311k | 299k | 5.4k | 1.7 h | 7.0 | £0.0018 | $0.015 |

Reasoning tokens: Ollama reports none separately, so they are counted in output.
