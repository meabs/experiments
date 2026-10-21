#!/usr/bin/env bash
# Rebuilds every analysis file from the committed raw runs, then runs the grading regression tests.
# Needs only Python 3 (and uv for pytest). The mutation results need Maven and the shopizer clone; see REPORT.md.
set -euo pipefail
cd "$(dirname "$0")/.."
R=results
python3 -I scripts/analyse.py $R/stage1/runs $R/stage1/bite.json > $R/analysis.md   # preregistered (also writes runs.csv)
python3 -I scripts/process.py $R/stage1/runs $R/retro/process.json                   # test-file-first and TDD evidence
python3 -I scripts/audit.py $R/stage1/runs hidden $R/retro/audit.json                # regrade from logs, isolation
python3 -I scripts/retro.py > $R/retro/analysis-retro.md                             # retrospective and exploratory
uv run --quiet --with pytest python -m pytest -q tests
# Optional, slow (about 40 minutes, needs JDK 21, offline ~/.m2 and $SHOPIZER):
#   python3 -I scripts/mutation.py $R/stage1/runs $R/retro/mutation.json --logs $R/retro/mutation-logs
