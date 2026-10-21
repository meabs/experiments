# Experiments

Agent experiments run with [AgentTrialRig](https://github.com/meabs/AgentTrialRig). One folder per experiment. Each folder has a `README.md` holding the design, written before any measured run, and a `results/` folder holding the raw runs and the analysis.

| Folder | Question | Status |
| --- | --- | --- |
| [2026-10-skills-impact](2026-10-skills-impact/) | Do popular agent skill packs (Superpowers, Matt Pocock's skills, pstack) change correctness or cost on a real Java repository? | Done: no pass-rate gain; Superpowers works test-first at 2–3x tokens ([results](2026-10-skills-impact/results/RESULTS.md)) |
| [2026-10-caveman](2026-10-caveman/) | Does the caveman skill cut tokens without losing correctness? | Design |
