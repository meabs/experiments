# Results

- [RESULTS.md](RESULTS.md): the answer and the hypothesis tests.
- [analysis.md](analysis.md): every table, produced by `scripts/analyse.py results/stage1/runs results/stage1/bite.json`.
- [runs.csv](runs.csv): one row per run.
- [report.md](report.md) and [plan.md](plan.md): AgentTrialRig's `report` and `plan` output.
- [stage1/](stage1/): raw runs. `raw.out.gz` is the agent's event log; `verify-mvn.log.gz` is the hidden-test build; `bite-mvn.log.gz` runs the agent's own BUG tests against the unfixed code (`scripts/bite.sh`). The home folder is replaced by `~`.
- [gate.md](gate.md) and [calibration.md](calibration.md): checks made before the measured runs.
