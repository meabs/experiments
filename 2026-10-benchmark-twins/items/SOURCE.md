# Item sources

- **GSM8K test set**: `grade_school_math/data/test.jsonl` from https://github.com/openai/grade-school-math (MIT licence),
  1,319 items, sha256 `3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14`, downloaded 2026-10-23.
- `gsm8k-twins.json`: built by `scripts/make_gsm8k_twins.py` from that file, with no language model. Its log, with the
  reasons items were skipped, is `make_gsm8k_twins.out`.
- **HumanEval**: `HumanEval.jsonl.gz` from https://github.com/openai/human-eval (MIT licence), 164 items, sha256
  `b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef`, downloaded 2026-10-23.
- `humaneval-twins.json` and `humaneval-twins-sample.json`: built by `scripts/make_humaneval_twins.py` from that file, with
  no language model; its log is `make_humaneval_twins.out`.
- `dryrun.json` (4 GSM8K items not among the twins) and `humaneval-dryrun.json` (the 2 HumanEval items left out): dry run only.
