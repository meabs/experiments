# Split the work, split the spec? Coding agents that divide a feature (Codex)

**Draft design, 2026-10-26. Not yet final: it is committed and pushed before any measured run, then changed only through the amendment log at the bottom.**

## Why

The [swarm-tax experiment](../2026-10-swarm-tax/REPORT.md) found that a planner–coder–reviewer team of Codex agents passed 25.7% of hidden acceptance tests on six features, against 56.8% for one agent. Most of the gap was the hand-off: only the planner saw the task, and its summary lost the details. Giving every agent the task file brought the team level (54.1%), at about 1.6 times the cost.

That team didn't really split the work: the planner handed the whole feature to one coder. The pitch for multi-agent coding is the split: a planner divides a feature into parts, coders build the parts at the same time, each with a focused brief. The user asked for this to be tested next ("Generate a report a test on this eg multiple coding agents", quoting the swarm-tax limit: "split into parts, with each coder given only the spec for its part").

So this experiment asks:

- does a team that splits a feature into parts, each coder given only its part's spec, beat one agent?
- does giving each coder only its part lose details at the seams, compared with letting every coder read the whole task?
- once every agent can read the whole task, does splitting beat a team with one coder?

## Agent and repository

As swarm-tax, unchanged:

- Codex `gpt-5.6-luna` (CLI 0.157), **medium reasoning effort in every arm and every subagent**. Team arms use Codex's own subagents (`--enable multi_agent_v2`), each spawned with `fork_turns "none"`.
- shopizer at `6a4a0a6` (Java, Maven, JDK 21), offline, each run in a fresh clone inside bubblewrap (`local-setup/codex-bwrap.sh`), which shows the agent only its own clone. The experiments folder and the hidden tests are invisible to it.
- Codex allows 4 agents at once, the planner included, so at most 3 coders can work at the same time.

## Arms

| Arm | Name | What the agent gets |
| --- | --- | --- |
| S | `solo` | The task prompt only |
| T | `team-spec` | swarm-tax's follow-up arm, unchanged ([`arms/team-spec.md`](arms/team-spec.md)): a planner (no editing) briefs one coder; a fresh reviewer checks the change; one round of fixes. The task is in the clone as `TASK.md`, and the coder and reviewer read it |
| P | `split-part` | A planner splits the feature into 2 or 3 parts that can be built at the same time, writes a part file for each (`.team/part-N.md`: what it does, the files it owns, **every requirement from the task that applies to it in the task's exact words**, and what the other parts provide), and spawns one coder per part, all at once. **Each coder reads only its own part file**, not `TASK.md` and not the other parts. A fresh reviewer reads `TASK.md` and checks the whole change; one round of fixes, each fault going to the coder whose part it is ([`arms/split-part.md`](arms/split-part.md)) |
| F | `split-full` | As P, but every coder reads `TASK.md` first and then its own part file, which says which part is its own; the planner doesn't copy requirements into the part files ([`arms/split-full.md`](arms/split-full.md)) |

- **P is the split as pitched:** focused coders with focused briefs. The planner's part files are written to disk, so, unlike the encrypted messages between agents, what each coder was told can be read and measured.
- **P against F** isolates the scoping: same split, same planner, same reviewer; the only difference is whether a coder sees the whole task or only its part.
- **F against T** isolates the split: every coder reads the whole task in both; F splits the work across coders working at the same time, T gives it to one coder.
- **S and T are rerun,** not taken from swarm-tax, so every arm runs in the same hours on the same service. Their swarm-tax scores (56.8% and 54.1%) are reported beside them as a check.
- **No best-of-k arm.** In swarm-tax no agent wrote a test and every attempt compiled, so a selector a user could apply couldn't tell attempts apart. Cost is reported instead, with cost per hidden test passed.
- **The planner may write only the part files.** The audit counts any planner command that edits a file outside `.team/`. The part files are kept beside each run (`team-parts/`) and left out of the graded diff ([`scripts/verify.sh`](scripts/verify.sh)).

## Tasks

swarm-tax's six features, unchanged ([`tasks/`](tasks/)), with the same hidden tests ([`hidden/`](hidden/)) and reference implementations ([`reference/`](reference/)), validated there before any run: with the reference applied every hidden test passes and the whole existing suite still passes. Reusing them makes the arms comparable with swarm-tax's. No agent has seen the hidden tests.

| Task | What it asks for | Hidden tests |
| --- | --- | --- |
| DISCOUNT | Merchant discount codes replacing a hard-coded promo rule | 16 |
| TIERPRICE | Quantity price tiers per product, applied to cart lines | 14 |
| WISHLIST | A logged-in customer's wishlist, move to cart, the store's most wished products | 15 |
| BACKINSTOCK | Back-in-stock alerts sent to an outbox when stock rises from zero | 13 |
| PRODUCTQA | Product questions with moderation | 14 |
| CARTLIMIT | Per-product purchase limits and store cart caps, with warnings on the cart | 14 |

## Size and cost

- 4 arms × 6 tasks × 6 runs = **144 runs**, the four trial files side by side, each 2 runs at a time.
- **API cost: about $20.** From swarm-tax: solo $0.073 and team-spec $0.116 per run; from the smoke test (below), split-part $0.163 and split-full $0.186.
- **Time:** about 4 to 6 hours. Time limits: 45 minutes for solo, 60 for the team arms. A run that times out is graded as it stands.

## Measures

**Primary: the share of hidden tests passed** per run (passed ÷ the task's hidden tests), from 0 to 1, **higher is better**. A run whose change doesn't compile scores 0.

**Secondary:**

- **Cost** at list prices, **tokens**, **wall time** (a split's selling point is coders working at the same time), **cost per hidden test passed**, verified passes (every hidden test and every existing test passes).
- **Did the split happen:** coders per run; runs where two or more coders' working times overlapped; part files written; planner edits outside `.team/`.
- **Did coders keep to their brief:** split-part coders who opened `TASK.md` or more than one part file; split-full and team-spec coders who opened `TASK.md`; runs where two or more coders patched the same file. From each coder's own commands in the session files ([`scripts/audit_run.py`](scripts/audit_run.py)).
- **Spec details carried through:** the share of the task's stated JSON field names and HTTP statuses that appear in the planner's part files, and in the change.
- **The rubber stamp rate:** final reviews that approved while hidden tests fail. **False success claims** (the rig's claim check).

## Hypotheses and analysis (fixed before the runs)

Arms are compared by the mean, over the 6 tasks, of each task's mean score, so every task counts equally.

| # | Hypothesis | Test |
| --- | --- | --- |
| H1 | `split-part` and `solo` differ: the split as pitched against one agent | Two-sided permutation test, arm labels shuffled within each task |
| H2 | `split-full` and `split-part` differ: what scoping each coder to its part costs or gains | As H1 |
| H3 | `split-full` and `team-spec` differ: what splitting the work gains once every agent reads the task | As H1 |

- Permutation tests: 100,000 random shuffles (seed 1), p = twice the smaller one-sided p. Effect intervals: bootstrap within tasks, 10,000 resamples (seed 1). H1 to H3 Holm-adjusted together at α = 0.05. Script: [`scripts/analyse.py`](scripts/analyse.py), which reuses swarm-tax's loader, permutation test and bootstrap unchanged.
- **How to read them, fixed now:**
  - **H1:** split-part above solo would be the first result in these experiments where a team beats one agent; below solo, the split as pitched loses.
  - **H2:** split-full above split-part means the planner's part files lose details at the seams, even when told to copy the requirements word for word; no measurable difference means the part files carried enough.
  - **H3:** split-full above team-spec means splitting the work helps once the task is shared; no measurable difference means the split buys nothing in score, and the comparison falls to cost and time.
- **The arm didn't happen as designed** if, in a split arm, fewer than half the runs have two or more coders, or, in split-part, coders opened `TASK.md` in more than a quarter of runs. That is reported instead of a verdict on the hypotheses that use the arm.
- **Power.** Six tasks is few. A difference under about 15 points will likely show as "no measurable difference", which means just that.

## Before the runs

1. **Smoke test. Done** (not counted): one split-part and one split-full run on CARTLIMIT and PRODUCTQA.

   | Run | Hidden tests passed (higher is better) | Coders (all three working at the same time) | Part files | Coders that opened `TASK.md` | First review | Cost (lower is better) | Time |
   | --- | --- | --- | --- | --- | --- | --- | --- |
   | split-part CARTLIMIT | 13/14 | 3 | 3 | 0 of 3 | CHANGES | $0.137 | 3.9 min |
   | split-part PRODUCTQA | 14/14 | 3 | 3 | 0 of 3 | CHANGES | $0.190 | 5.3 min |
   | split-full CARTLIMIT | 12/14 | 3 | 3 | 3 of 3 | CHANGES | $0.201 | 4.1 min |
   | split-full PRODUCTQA | 14/14 | 3 | 3 | 3 of 3 | CHANGES | $0.172 | 4.7 min |

   - Mean cost per run: split-part $0.163, split-full $0.186; median 4.6 and 4.4 minutes. With solo and team-spec at swarm-tax's costs, the 144 runs come to about $20.
   - Every split-part part file copied the task's requirements word for word (all of the stated fields and statuses appear in them); a sample, CARTLIMIT part 1, lists its files, quotes three requirements and names what the other parts call.
   - No coder patched a file another coder patched, no planner edited source, every spawn used `fork_turns "none"`.
   - **Audit fix found here:** a split-part coder ran `rg … --glob '!TASK.md'`, a search that excludes the file, and the first audit counted it as opening `TASK.md`. The check now ignores a mention preceded by `!`, and still counts reads by absolute path (tested).
   - **Ceiling risk, noted and not acted on:** these two tasks scored high in the smoke runs, and one agent already passed 91.7% of PRODUCTQA in swarm-tax, so PRODUCTQA leaves little room above solo. The tasks are not changed after seeing this.
2. **Analysis script run on the smoke runs. Done.** Every section ran on the four smoke runs together with swarm-tax's solo and team-spec runs (used only to exercise the script).
3. **Design committed as final and pushed, then run,** after the user's OK.

## Known limits

- One repository, one model at one effort level, six features, and team instructions I wrote. The tasks and hidden tests are reused from swarm-tax.
- "Coders read only their part" is an instruction, checked afterwards from each coder's commands; the sandbox can't hide `TASK.md` from coders while showing it to the reviewer. A coder that searched the whole clone without naming the file would not be counted.
- The planner decides how to split. Some features split less naturally than others; the split chosen is reported.
- **No local model,** as in swarm-tax, at the user's direction ("Use codex and Luna model"): a local model could not finish these features in reasonable time.

## Reproducing

```
python3 -I scripts/make_trial.py                     # the four trial files (--smoke TASK,TASK for the smoke files)
scripts/run_all.sh <out dir>                          # the four side by side, with the Maven checksum before and after
python3 -I scripts/analyse.py <out dir>/solo <out dir>/team-spec <out dir>/split-part <out dir>/split-full > results/analysis.md
```

## Amendment log

- 2026-10-26: draft design written at the user's request ("Merge and start the next experiment"), after swarm-tax's write-up was merged. Tasks, hidden tests, references, grader, sandbox and analysis code reused from swarm-tax; `verify.sh` also keeps the planner's part files and leaves them out of the graded diff; `audit_run.py` also records, per coder, what it read, the files it patched and when it worked.
- 2026-10-26: smoke test run and recorded ("Before the runs"); the audit's `TASK.md` check corrected so a search that excludes the file doesn't count as reading it.
