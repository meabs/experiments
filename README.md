# Experiments

Agent experiments run with [AgentTrialRig](https://github.com/meabs/AgentTrialRig). One folder per experiment. Each folder has a `README.md` holding the design, written before any measured run, and a `results/` folder holding the raw runs and the analysis.

| Folder | Question | Status |
| --- | --- | --- |
| [2026-10-skills-impact](2026-10-skills-impact/) | Do popular agent skill packs (Superpowers, Matt Pocock's skills, pstack) change correctness or cost on a real Java repository? | Done: no pass-rate gain; Superpowers works test-first at 2–3x tokens ([report](2026-10-skills-impact/REPORT.md)) |
| [2026-10-caveman](2026-10-caveman/) | Does the caveman skill cut tokens without losing correctness? | Done (Codex): output down 13%, total saving not shown, correctness held ([report](2026-10-caveman/REPORT.md)) |
| [2026-10-skills-tasks](2026-10-skills-tasks/) | Across 16 different tasks at low effort, do Superpowers or Pocock's skills raise the pass rate? | Done (Codex): no significant gain (Pocock 27/32, Superpowers and control 24/32); Superpowers 3.1x tokens; 28 of 30 failures claimed success ([report](2026-10-skills-tasks/REPORT.md)) |
| [2026-10-verify-vs-skills](2026-10-verify-vs-skills/) | Which buys more correct changes per dollar: a short instruction to verify against the running app, the Superpowers pack, or more reasoning effort? | Done (Codex): only medium effort helped (49/60 vs 36/60, Holm p 0.041); verify 39/60 and Superpowers 37/60 not significant; the app could not start outside its tests, so verify rarely checked it ([report](2026-10-verify-vs-skills/REPORT.md)) |
| [2026-10-repo-skills](2026-10-repo-skills/) | Does repository-specific guidance (an agent-written AGENTS.md and skills) raise the pass rate over no guidance? | Guidance generated; runs in progress |
