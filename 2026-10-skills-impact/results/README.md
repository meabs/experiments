# Results

- [../REPORT.md](../REPORT.md): the engineering report (method, preregistered results, retrospective review, defects, validity).
- [analysis.md](analysis.md) and [runs.csv](runs.csv): the preregistered analysis (`scripts/analyse.py`), one row per run.
- [retro/analysis-retro.md](retro/analysis-retro.md): the retrospective and exploratory analysis (`scripts/retro.py`), built from:
  - `retro/mutation.json` and `retro/mutation-logs/`: per-defect mutation testing (`scripts/mutation.py`);
  - `retro/process.json`: test-file-first and confirmed TDD (`scripts/process.py`);
  - `retro/audit.json`: the independent regrade and isolation search (`scripts/audit.py`).
- [report.md](report.md) and [plan.md](plan.md): AgentTrialRig's `report` and `plan` output.
- [stage1/](stage1/): raw runs, unchanged since the run. `raw.out.gz` is the agent's event log, `verify-mvn.log.gz` the hidden-test build, and `bite-mvn.log.gz` the original tests-that-bite run.
- [gate.md](gate.md) and [calibration.md](calibration.md): checks made before the measured runs.

`scripts/reproduce.sh` rebuilds every file above except the mutation results, which need Maven.
