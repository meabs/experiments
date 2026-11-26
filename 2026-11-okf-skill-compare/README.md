# OKF skill comparison (a test)

Compares the owner's `okf-interview` skill with Google's `okf-generate` and `okf-consume` (OKF v0.3) on a small synthetic fixture,
5 runs each. Design in one paragraph: the agent gets `fixture/client.py` and `fixture/notes.md` (seven answers, four of them
"unknown"), writes a bundle with one skill, then a second agent answers `fixture/questions.md` from it. Scored from files by
`scripts/analyse.py`. Results and caveats in [FINDINGS.md](FINDINGS.md). Written after the design was fixed and before any scoring;
the first scoring pass was corrected by hand (see FINDINGS). Pilot: one run of the owner's skill (`results/pilot`).
