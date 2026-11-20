# Attack my architecture: do patches make it safer, or just bigger? (AMA)

**Status:** run on 2026-11-20 (two local models, 48 games each); results in [REPORT.md](REPORT.md). Designed and run by an AI agent at Garry Meaburn's request; the owner approved the design and the main run. Later changes go in the amendment log (section 10).

## 1. Question

1. When every successful attack on a system architecture is followed by a defender's change to the live architecture,
   does the number of working attack paths fall, or does the system just accumulate parts?
2. Does the kind of change the defender is allowed to make (any change, only removals and narrowing, or the minimal
   fix of the exact step used) alter the answer?
3. How often does a fix break something the business needs?

## 2. Why it is worth testing

Security advice for agent systems is mostly "add a layer" (gateway, vault, broker, approval step). Each layer is also
a new component, credential and trust boundary. Nobody here has measured whether iterated, attack-driven patching
converges. Related, already run: [agent-identity](../2026-10-agent-identity/) (which identity pattern holds),
[guard-damage](../2026-11-guard-damage/) (a guardrail that blocked commands but not harm). Neither tested a design
that changes under attack. If free patching wins, "let the defender agent redesign" is a sound loop. If paths fall
only for the minimal or subtractive defender, complexity is the cost to watch.

## 3. What is being changed: the arms

The architecture is a **declarative model** (JSON): components (APIs, agents, stores, humans), credentials (who holds
what, scope, lifetime), edges (calls, with the credential they need) and trust boundaries. A deterministic engine
decides whether a step is allowed. Nothing real is attacked; no network, shell or file tool is given to either agent.

| Arm | Defender after each verified attack | Else constant |
| --- | --- | --- |
| N | No change (the red agent keeps attacking a static system: baseline for discovery and saturation) | |
| F | Free: proposes a JSON patch that may add, remove or change anything | |
| S | Subtractive: may remove or narrow only (revoke, shorten lifetime, cut an edge, tighten scope); may not add components, credentials or edges | |
| M | Scripted minimal: revokes only the exact credential or edge the attack used (no model) | |

Held constant: red and defender are the local model `qwen3.8:27b` (Ollama 0.40.14, Q4, thinking off, temperature 0.7, seed fixed per call, 8,192 context), same prompts except the defender's allowed edit
set, the same starting architectures, the same rounds, one turn per call. Red sees the **documented** model
(components, edges, credentials, boundaries) and not the engine's list of weaknesses; it proposes a step sequence and
the engine says which steps succeed. The defender sees the successful path
and the live model.

## 4. The fixtures

Four fictional systems from a generator (`scripts/make_arch.py`, seeded), each with 10 to 14 components, an
internet entry, three crown jewels (customer data, secrets vault, payments), an agent that holds credentials and reads
untrusted input, and 3 to 6 planted weaknesses (shared key, over-scoped agent token, confused-deputy edge, long-lived
credential, flat network zone) of different depth. Each also lists 6 **business flows** that must stay possible.

**Rules as built** (`scripts/engine.py`): the attacker starts as the internet and can (a) *access* a component over an
edge it may use (no credential, a stolen one, or the edge's own holder already controlled), (b) *relay* untrusted text
along an edge to an agent, (c) *take over* a component that has an unmitigated weakness (`injectable` or `rce`) once
it has access, (d) *steal* a credential held in plaintext by a controlled component, or one in a vault if the vault is
controlled. Short-lived credentials cannot be stolen. A mitigation (`input_filter`, `approval_gate`, `patched`,
`sandbox`) switches a weakness off. Patch operations are add/remove component, edge, credential, set edge scope or
credential, add mitigation; the subtractive arm may only remove or narrow.

**Independent verifier:** `scripts/engine.py` enumerates every attack path (entry to a crown jewel, up to 8 steps) by
exhaustive search of the rules. The red agent's success is only what the engine confirms; "security" is the count of
engine-found paths, never the agents' view of it. It also replays the business flows after each patch.

**Free checks (no model), before any spend:** self-test applies, to each fixture, a known attack (must succeed), the
exact fix (path must vanish, flows intact), a harmful shortcut (delete the database edge: paths vanish but flows
break, verifier must say so), an invalid patch and a forged step (both rejected). Canary: scripted red and defenders (`scripts/demo.py`, no model) play the same fixtures; the no-defender path count must stay
constant, the minimal-fix count must never rise, and no flow may break.

**Pilot rule:** one pilot game per arm N on each fixture. A fixture where red finds no verified path in under a
third of rounds is redesigned; where red succeeds in every round with no defence and one trivial path, it is retired
(`PILOT-ONLY`). Pilot data are not pooled with main.

## 5. Measures

Primary: **exhaustive attack-path count** after each round (engine), final versus start.
Secondary, all from the engine and ledger: red success per round (a breach counts if the steps that worked reach a crown jewel; failed side steps are ignored and the defender sees only the verified steps); **complexity** (components + edges + credentials +
rules, and added minus removed items per patch); **paths removed per item added**; business flows broken after each
patch; patches rejected as invalid; new paths a patch created; tokens and cost at list price ($0.20 input, $0.02
cached, $1.20 output per million). Per-round records are `ledger.jsonl`, final models are `final.json`.
Whether a defender's stated reason was right is not measured.

**Graphical observer (added 2026-11-20, before any model call).** `diagrams/observer.template.html` is a
self-contained page that replays any recorded game: the architecture laid out by trust zone, red's path lighting up
step by step, the defender's patch drawn as additions (green) and removals (red, dashed), and live charts of
attack paths and complexity for every defender arm on the same system. `scripts/build_viewer.py` bakes a games file
into one HTML page. The page replays the engine's records only; it computes no result. It is also how Garry can watch a
real run. The built `observer-demo.html` uses scripted players (`scripts/demo.py`, no model) and is marked DEMO in its
header; those games are not data.

## 6. Hypotheses and analysis

Written before any run, directional:

- **H1** Free defender (F) ends with fewer engine paths than it started with. Predicted: yes, but by less than S.
- **H2** F ends with more complexity than S and M, and more than it started with (predicted: components rise by 3 or
  more); paths removed per item added is lower for F than for S.
- **H3** F breaks at least one business flow in a larger share of games than S (predicted 30% vs under 10%).
- **H4** In F, at least one patch creates a path that did not exist before (new surface), in more than a third of games.
- **H5** Red succeeds in later rounds more often against N (static) than against F or S (the loop helps at all).

Test: unit is the game; score is the mean over fixtures of each fixture's mean; one-sided permutation within fixture
(100,000 shuffles, seed 1), bootstrap 95% intervals within fixture (10,000, seed 1), Holm correction within each
hypothesis group. Four fixtures give weak power; claims about difference need the interval to exclude zero. Anything
added after seeing data is labelled exploratory. Analysis: `scripts/analyse.py` writes `analysis.json`, `runs.csv`.

## 7. Size, cost and time

Games = 4 fixtures x 4 arms x 3 repetitions = 48 (M and N: red only). Up to 8 rounds each, red up to 3 calls a round,
defender up to 2 in F and S. Pilot: 4 N games (one per fixture), about 15 minutes. Games run one at a time (one local
model), arms and fixtures interleaved so a partial result is balanced. Runs use the local model through Ollama's chat API (owner's instruction, 2026-11-20), not Codex: each turn is one
JSON-only call, there is no tool, shell or file access, so the repo's Codex sandbox does not apply. Red gets up to three
attempts a round and is told after each which steps worked. A game stops early after two rounds with no engine path left
(never in arm N). Measured in the smoke test: about 9 s a call, 30 to 60 s a round, so a game takes 3 to 5 minutes and the
48 games about 3 to 4 hours, one at a time. Provider cost is **$0** (no ceiling needed); electricity is not measured.
Tokens are recorded per call (`calls` in each game file) and are the only cost figure reported.

## 8. Rounds

Round 2 could add held-out fixtures, a stronger red model, a defender that must also keep a complexity budget, and
real software (a small compose stack) in place of the model.

## 9. Limits known in advance

A model of an architecture, not running systems: realism depends on the engine's rules, and red can only find what
they allow. One model family, four generated systems, three repetitions. The defender sees only paths red found, a
realistic limit but it favours M. Complexity counts are a proxy. Games within a fixture are not independent of the
fixture's weaknesses. No claim about real organisations or about human red teams.

## 10. Amendment log

- 2026-11-20, owner asked for the same experiment on `huihui_ai/Qwen3.8-abliterated:latest` (Ollama digest bdc5e13cd164, 17 GB,
  the model downloaded for the agent-society experiment) to compare models. Queued to start when the `qwen3.8:27b` main run
  ends: identical design, prompts, seeds, fixtures and arms (`scripts/main-huihui.sh`, results in `results/main-huihui/`).
  Each model is analysed on its own; the comparison between models is exploratory. An abliterated model has had its refusal
  behaviour removed, so a difference from the stock model may come from that, from a different base, or from chance with 12
  games per arm. Added before any `qwen3.8:27b` result was analysed.

- 2026-11-20, owner approved; design frozen. Main run started (`scripts/main.sh`, reps 1 to 3 into `results/main/`, arms F, S, M, N).

- 2026-11-20, pilot done (`results/pilot/`, PILOT-ONLY, not pooled): one no-defender game per system, 8 rounds, local
  model. Red breached a crown jewel in 8 of 8 rounds on every system (A, B, C, D), mostly on its first attempt, with
  attacks of 4 to 5 verified steps against 2 or 3 engine-found paths. Pilot rule: no system is below a third, and none is
  a single trivial path, so none is retired or redesigned. Observation, not a finding: with no defender red repeats the
  same attack each round (arm N is a saturation baseline). 82 model calls, about 68,000 prompt and 4,500 output tokens.

- 2026-11-20, before any pilot: owner said to use a local Ollama model. Switched from hosted Luna to `qwen3.8:27b` through
  Ollama chat (`scripts/run_game.py`); section 3, 7 updated, cost now $0. A smoke test of 2 rounds in arms N and F ran to check
  the runner (`results/smoke/`, not data). It showed red's strict all-steps rule scored a real breach as a failure when a
  side step failed, so `engine.simulate` now returns the jewel reached by the steps that worked. Before any pilot.
- 2026-11-20, before any model call: owner asked for the work to be graphical and engaging. Added the replay observer
  (section 5), the engine and four fixtures (`scripts/engine.py`, `scripts/make_arch.py`; 40 self-test checks pass,
  `scripts/selftest.py`), and the engine rules text in section 4. Fixture weaknesses were adjusted while building so
  every system has 2 or 3 verified attack paths at the start (the first draft had none reachable from the internet);
  no model had been run. Still open: the model-call route (Codex or direct), the red and defender prompts, the runner,
  the canary and the pilot.
