# Arm E changelog

E changes only when a **newly published finding from another experiment** supports adding, changing or removing a
setting (README section 7). Nothing in this file is changed because of what ELC's own runs show.

## v1 (2026-11-04, round 1)

The settings and the finding behind each are in the README's arms table (section 3). In short:

- Repository AGENTS.md, three lines: `mvn -o test` without quiet mode; check how many tests ran and failed; follow the
  code when docs disagree (BRK-1; B3, OKS, OKF; short guidance per DOCLAYER and J).
- User-level `~/.codex/AGENTS.md`: repo-injection's paragraph (RI).
- Sub-agents off, `--disable multi_agent` (SWT, SPS).
- Stop-hook gate: builds and runs the whole existing suite, sends the agent back once on a failure or fewer than 40
  executed tests (TSK, SEC, BRK-2). An extrapolation, not a tested setting in this form.
- Left out, with reasons: README section 3, "Findings left out of E v1".

Round 1 result for v1: [REPORT.md](../../REPORT.md).
