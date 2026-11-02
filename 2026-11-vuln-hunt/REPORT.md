# Coding agent or specialist security agent? Report

2 November 2026. Design: [README.md](README.md), pushed before the app was written (56238dba); the app, answer key,
harness, pilot and amendments were pushed before the main run (5af45184). Full numbers:
[results/analysis.md](results/analysis.md). Checks: [results/checks.md](results/checks.md). Every run's findings,
tool calls, cost and the judge's labels: [`results/main/`](results/main/).

## 1. What I wanted to find out

Given a web app with planted vulnerabilities, from easy to very hard to spot, does a security specialist agent find
more of them than an ordinary coding agent asked to review the code? And does a team of specialists find more than
one specialist?

- **Coding agent:** Codex CLI, as it comes.
- **Specialist agents:** built with [Strands Agents](https://strandsagents.com) on OpenRouter, with the same model as
  Codex.

## 2. Why I thought it was worth testing

"Use a specialist agent for security" and "use a team of agents" are both common advice. General coding agents are
already asked to "review this for security" every day. If a purpose-built agent finds much more, that's worth
building. If it doesn't, the coding agent you already have is enough. The test covers all ten OWASP Top 10:2025
categories, so it shows which kinds of problem each approach misses.

## 3. What I predicted

Fixed before any measured run (H4 was added and H2 reworded after the pilot, before the main run; see the README's
amendment log). All use `gpt-5.6-luna`:

1. **H1:** the Strands specialist (B) finds more hard and very-hard vulnerabilities than Codex (A).
2. **H2:** the Strands specialist team (C, a Graph) finds more hard and very-hard vulnerabilities than the specialist
   (B).
3. **H3:** the specialist (B) has higher precision than Codex (A).
4. **H4:** Codex given the specialist's checklist (A2) finds more hard and very-hard vulnerabilities than plain Codex
   (A).

## 4. How I tested it

- **The app:** a small Flask shop API (about 1,200 lines) with 23 planted vulnerabilities. It covers all ten OWASP
  Top 10:2025 categories: easy 3, medium 6, hard 9, very hard 5. It also has 6 decoys, code that looks risky but is
  safe. A pytest proof shows each vulnerability on the running app, and each decoy is tested as safe. The agents never
  see the key or the proofs.
- **Same task text for every arm:** "Review this repository for security vulnerabilities. Write each finding to
  `FINDINGS.json`… Only report what you believe is a real vulnerability."
- **Five arms:**

  | Arm | What it is |
  | --- | --- |
  | A. Codex | Codex CLI 0.164 as it comes, in a sandbox with a shell. Web search off |
  | A2. Codex + checklist | The same, with B's specialist instructions and a running copy of the app |
  | B. Strands specialist | One agent with a security-reviewer prompt (a checklist following OWASP's categories; evidence required) and four tools: list files, read a file, search the code, send HTTP requests to a running copy of the app |
  | C. Strands team (Graph) | A recon agent, then four specialists in parallel (injection; access control and authentication; cryptography, configuration and dependencies; logic, integrity, logging and errors), then a verifier that checks and submits. The order is fixed in code. Same tools as B |
  | D. Strands swarm | The same six roles, but the agents choose who goes next by handing off (Strands' `Swarm`). Descriptive only |

- **Model:** `gpt-5.6-luna` at medium reasoning effort for every arm: Codex through OpenAI, Strands through
  OpenRouter's Responses API. B and C were also run with `qwen/qwen3.7-flash` as a cheap replication.
- **Size:** 10 runs of each of A, A2, B, C, D with Luna, plus B and C with Qwen: **70 runs**.
- **Scoring:** a judge model (`gpt-6-luna`) matched each of the 822 findings to the answer key. I read all 822
  labels, agreed with 811, and used my own label for the other 11.
- **Tests:** the unit is the vulnerability. For each of the 14 hard and very-hard vulnerabilities, each arm has a
  detection rate over its 10 runs. The paired differences between arms get an exact one-sided sign-flip test and a
  bootstrap 95% interval. Holm correction over H1–H4.

## 5. What happened

**Planted vulnerabilities found per run** (mean of 10 runs; **higher is better**):

| Arm | Hard + very hard (of 14) | All (of 23) | Worst and best run, hard + very hard |
| --- | --- | --- | --- |
| A. Codex | 7.1 | 11.1 | 5–8 |
| A2. Codex + checklist | 7.8 | 12.9 | 6–9 |
| B. Strands specialist | 5.8 | 10.9 | 4–8 |
| **C. Strands team (Graph)** | **10.9** | **16.7** | **9–12** |
| D. Strands swarm | 4.4 | 7.2 | 0–7 |
| B. Strands specialist, Qwen | 5.2 | 10.4 | 4–6 |
| C. Strands team, Qwen | 4.6 | 9.2 | 0–9 (4 of 10 runs crashed) |

**The hypotheses** (difference in the hard and very-hard detection rate, percentage points; Holm-adjusted p):

| Hypothesis | Difference | 95% interval | Holm p | Verdict |
| --- | --- | --- | --- | --- |
| H1: B > A | −9.3 | −27.1 to +7.9 | 1.0 | **Not supported.** The specialist found no more than Codex, if anything fewer |
| H2: C > B | **+36.4** | +25.0 to +47.9 | **0.001** | **Supported** |
| H3: precision B > A | 0 | – | 1.0 | **Not supported:** neither made a single false claim |
| H4: A2 > A | +5.0 | −7.1 to +15.7 | 0.74 | **No measurable difference** |

Descriptive (no test): Codex + checklist against the Strands specialist (A2 − B, the same instructions and model)
+14.3 points (+5.0 to +23.6). Swarm against Graph team (D − C) −46.4 points.

**By OWASP Top 10:2025 category** (mean share of the category's planted vulnerabilities found per run, Luna; **higher
is better**):

| Category | A | A2 | B | C | D |
| --- | --- | --- | --- | --- | --- |
| A01 Broken Access Control | 53% | 67% | 53% | **90%** | 40% |
| A02 Security Misconfiguration | **0%** | 20% | 45% | 25% | 5% |
| A03 Software Supply Chain Failures | 0% | 10% | 0% | 20% | 0% |
| A04 Cryptographic Failures | 67% | 77% | 70% | **100%** | 47% |
| A05 Injection | 97% | 83% | 70% | **100%** | 77% |
| A06 Insecure Design | 5% | 5% | 0% | **40%** | 0% |
| A07 Authentication Failures | 45% | 55% | 40% | 65% | 25% |
| A08 Software or Data Integrity Failures | 90% | 95% | 65% | **100%** | 45% |
| A09 Security Logging & Alerting Failures | 15% | 40% | 20% | 50% | 0% |
| A10 Mishandling of Exceptional Conditions | 75% | 80% | 85% | **100%** | 40% |

Per vulnerability: [results/analysis.md](results/analysis.md).

**False alarms** (findings that weren't real; **lower is better**): none in any Luna run, in 606 findings. With
Qwen, 12 in 216. Real issues I hadn't planted (28 findings, mostly from C) were counted separately, not as false
alarms.

**Cost and time** (per run, list prices; **lower is better**):

| Arm | Cost | Median time | Tool calls |
| --- | --- | --- | --- |
| A. Codex | $0.016 | 44 s | 10 (shell commands and edits) |
| A2. Codex + checklist | $0.024 | 74 s | 18 |
| B. Strands specialist | $0.015 | 72 s | 36 |
| C. Strands team (Graph) | $0.064 | 180 s | 129 |
| D. Strands swarm | $0.027 | 157 s | 52 |
| B. Strands specialist, Qwen | $0.008 | 304 s | |
| C. Strands team, Qwen | $0.055 or more | 20 min | |

All 70 runs cost $2.09, and the judge $0.32.

## 6. What surprised me

- **The specialist prompt alone didn't help.** The single Strands specialist found fewer hard ones than plain Codex
  (5.8 against 7.1). Giving Codex the same checklist didn't measurably help either (+5 points, not significant). The
  specialist opened every file holding a hard vulnerability in every run, so it wasn't missing them for lack of
  reading. It just didn't spot some: the second-order SQL injection in 2 of 10 runs (Codex: 10 of 10), the image
  redirect SSRF in 0 (Codex: 5).
- **With the same instructions and model, Codex's harness beat Strands'.** A2 (Codex + checklist) found 14 points
  more than B (the Strands specialist) on the hard ones. Codex has a shell and its own system prompt; I can't separate
  those.
- **Splitting the review between specialists, in a fixed order, was the big win.** The Graph team found 10.9 of the
  14 hard ones, against 5.8 for one specialist. Its worst run (9) beat Codex's best (8). It was the only arm to find
  the design flaws regularly:
  - returns ignoring items already cancelled and refunded (40%, others 0–10%);
  - the gift-card race (40%, the other Luna arms 0%);
  - the dependency-confusion setup (40%).
- **The Swarm, with the same six roles, was the worst arm.** Agents in a Strands Swarm choose who goes next. Two of
  the four specialists (cryptography/config/dependencies and logic/integrity/errors) never ran in any of the 10 runs.
  In 6 runs the injection specialist handed straight to the verifier; one run ended without submitting anything. Same
  agents, same prompts: the only difference from the Graph is who decides the order.
- **No false alarms at all with Luna.** In 606 findings, not one was wrong or flagged a decoy. Every arm found what
  it found and stayed quiet otherwise. So precision didn't separate the arms (H3); recall did.
- **Plain Codex never reported the obvious configuration problems.** `debug=True` and CORS reflecting any origin
  with credentials were found in 0 of 10 plain Codex runs, against 30–60% for the Strands specialist. It went for
  code bugs.
- **Two planted vulnerabilities were found by nobody in 70 runs:** a pinned PyJWT version with a published CVE, and
  refunds being the one admin action not written to the audit log.
- **Qwen couldn't drive the team.** With Qwen, 4 of 10 Graph runs crashed on a dropped connection or after hundreds
  of tool calls, and runs took about 20 minutes. Strands doesn't retry a dropped model connection, so one network
  blip ends the whole team's run. The Qwen specialist alone was steady and cheap ($0.008), finding about as much as
  the Luna specialist.
- **Running Codex several times closes much of the gap** (worked out after the results; not a planned comparison).
  The 10 Codex runs found different things. Combining 4 Codex runs costs the same as one Graph run ($0.063) and finds
  9.4 hard ones. 3 runs of Codex + checklist ($0.072) find 10.4 of the hard ones and 16.7 in all, close to the Graph
  team's 10.9 and 16.7.

## 7. What this might mean in practice

### Impact

For a security review of a small codebase, a coding agent like Codex already does about as well as a single
specialist agent built for the job, and makes no false claims. A specialist system prompt, on its own, wasn't worth
building. What found more was **structure**: separate specialists each covering one area in full, run in a fixed
order, with a verifier at the end. That found half as many again of the hard vulnerabilities as Codex, including design flaws
the single agents mostly missed, for about 5 cents a review.

The same team, left to hand work between themselves, skipped half the specialists and did worst of all. If you build
a multi-agent reviewer, the order belongs in code.

### Configuration recommendations

| Recommendation | Why | Strength |
| --- | --- | --- |
| For a thorough security review, run fixed specialists (one per area) in parallel and a verifier after them, with the order set in code | Graph team found 10.9 of 14 hard ones against 5.8 for one specialist; worst team run beat Codex's best | Strong: H2, Holm p = 0.001 |
| Don't expect a "security expert" system prompt on a single agent to beat a general coding agent | The Strands specialist found fewer than Codex (H1 not supported); a checklist didn't measurably help Codex (H4) | Tested, no effect found |
| Don't let agents choose the review order (Swarm-style handoffs) | The Swarm never ran two of its four specialists and found the fewest | Descriptive; 10 runs |
| If you use a coding agent, run it several times and merge the findings | 3 Codex + checklist runs (7 cents) came close to the Graph team; runs found different things | Descriptive, worked out after the results |
| Check dependency versions against an advisory database (e.g. `pip-audit`) and check audit logging with a tool or test, not an agent | No run in 70 flagged the vulnerable PyJWT pin or the missing refund audit entry | Descriptive |
| Add retries around the model connection in Strands multi-agent runs, and set time limits | 4 of 10 Qwen Graph runs died on one dropped connection or after hundreds of tool calls | Descriptive |

### Risks this exposes

- **A clean review isn't a clean bill of health.** Every arm missed things, with no false alarms to warn you. A single
  Codex run left about half the hard vulnerabilities unreported, and nothing said they were missing.
- **Some classes are close to invisible to all of these agents:** a known-vulnerable dependency version, a missing
  audit log entry, dependency confusion, and races. A06 (insecure design) and A03 (supply chain) were found least.
- **Handoff-based swarms can fail silently.** The Swarm's runs reported "completed" whether or not the specialists
  ran. Without checking which agents ran, you'd think the whole checklist was covered.

## 8. What the experiment does not prove

- **I wrote the app, the vulnerabilities, the decoys and the specialist prompts,** knowing the bugs. The checklist
  follows OWASP's categories, but some items are close to planted bugs. That favours B, C and D, and B still didn't
  beat Codex.
- **Planted bugs in a small app aren't real-world code.** 23 vulnerabilities in 1,200 lines is dense. A large
  codebase would test reading and search far more.
- **One model and one cheap model, at one effort level.** Codex's model, harness and system prompt come as a package.
  B and C's tools are four simple functions; a Strands agent with a shell might do better.
- **The Graph team has more structure and more calls,** and the comparison is at the default settings, not equal
  spend. Combining several Codex runs (section 6) narrows the gap, but that comparison wasn't planned.
- **Codex had network access** (it reaches its model over it), with web search off. The app's source is in a public
  repository, but the review ran on a copy, and none of the agents searched the web.
- **The judge is a model,** though I checked all 822 of its labels and changed 11.

## 9. What I'd test next

- **Equal spend:** Codex run N times and merged, against one Graph team run, as a planned comparison.
- **A Graph team built on Codex:** four Codex runs, each given one specialist's area, plus a verifier. That would
  separate the team structure from the Strands harness.
- **A real codebase** with known, published vulnerabilities, rather than planted ones.
- **Tools in the loop:** give each arm `pip-audit` and a static analyser, and see whether the never-found
  vulnerabilities get found.

## 10. How to reproduce the results

```
python3 -I -m pytest key/test_proofs.py                     # the 23 proofs and 6 decoy tests, against target/
python3 -I src/run.py new <run> --arm A|A2|B|C|D --model luna|qwen; python3 -I src/run.py go <run>
python3 -I src/batch.py                                     # the 70 main runs (needs Codex, the Strands venv and ~/.config/openrouter.key)
python3 -I src/judge.py <work dir>/main
python3 -I src/analyse.py <work dir>/main > results/analysis.md
python3 -I src/analyse.py results/main                      # the same tables from the exported data
```

## 11. What changed from the design

All recorded in the README's amendment log, with the user's words where they asked for a change:

- **Before the pilot:** tier counts corrected (hard 9, very hard 5); PyJWT 2.3.0 pinned for V06; Strands moved to
  the Responses API; the judge got an "outside the key" label.
- **During the pilot:** arm A2 (Codex + checklist) and H4 added, at the user's request.
- **After the Swarm failed in the pilot:** the specialist team became a Strands Graph (C, tested by H2), and the
  Swarm became a descriptive arm (D). The user chose this.
- **After the pilot, from its cost:** 10 runs per arm instead of 5 (70 runs).
- **After the main run:** crashed runs are counted as finding nothing (not stated in the design). `batch.py` was
  written before the main run but committed after it; `analyse.py`, `export.py` and my hand labels were written
  during and after it.
