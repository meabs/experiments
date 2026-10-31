# Grill me first? Report

31 October 2026. Design: [README.md](README.md), committed and pushed (5f640385) before any run; the build and
pre-run amendments were pushed (9ebb04a0) before the main run. Full numbers: [results/analysis.md](results/analysis.md);
checks: [results/checks.md](results/checks.md); every run's dialogue, labels, grade and diff: `results/main/`.

## 1. What I wanted to find out

Matt Pocock's `grilling` skill makes a coding agent interview you before it builds anything: numbered rounds of
questions, each with the agent's own recommended answer, until you both agree what's wanted. `grill-with-docs` does
the same and also writes what was settled into the repository (a glossary and short decision records, ADRs). I wanted
to know:

1. Does grilling build more of what the developer actually wanted than working from the ticket alone?
2. Is that from the skill, or just from being allowed to ask ("ask me anything first")?
3. Is it from the developer's answers, or from the agent's own recommendations (a developer who says "yes" to
   everything)?
4. Where is it worth the developer's time: tickets that leave out nothing, a little, or a lot?
5. Do grill-with-docs's docs help the *next* ticket, in a fresh session with nobody to ask?

## 2. Why I thought it was worth testing

Every ticket leaves things out: the business rule everyone "just knows", the decision made in a meeting. An agent
working from the ticket can only guess. Grilling is a popular answer, and it's easy to believe. It also costs the
developer time, and an agent that offers a recommended answer invites a busy developer to just say yes. I could find
no measurement of what the interview actually gets you, or where it stops paying.

Following the backlog rule, the experiment was built so that grilling *should* win: four of the six tickets leave out
requirements that only the developer knows.

## 3. What I predicted

Fixed before any run (README):

1. On the tickets that leave out the most, grilling (G) meets more left-out requirements than ticket only (T).
2. Grilling against "ask me anything first" (Q): no direction predicted.
3. On the requirements only the developer knows, G beats grilling with "yes" to everything (GY), and GY is no better
   than T.
4. On clear tickets, G is no better than T and costs more.
5. In stage 2, the docs meet more of the follow-up's left-out requirements than no docs.

## 4. How I tested it

- **App and agent:** a small multi-tenant Spring Boot banking API (accounts, notes, support cases; 25 existing
  tests). Codex CLI 0.157.0 with hosted `gpt-5.6-luna` at medium effort, in a bubblewrap sandbox. One Codex session
  per run; each developer reply goes back into the same session.
- **Six tickets,** two at each level:
  - **Clear** (C1, C2): nothing left out.
  - **Some** (S1, S2): two requirements left out, one findable in the repo, one only in the developer's head.
  - **Lots** (L1, L2): four left out, two in the repo, two in the developer's head. One of L2's (rd) turned out to be
    guessable and is kept out of hypothesis 3, as decided before the main run.
  - An example of an "in my head" requirement: S1 adds notes to accounts, and support users may only add *internal*
    notes, because anything a customer sees counts as a message from the bank and must come from an admin.
- **Five arms,** 3 runs per ticket, 90 runs:

  | Arm | What the agent got | Who answered |
  | --- | --- | --- |
  | T | The ticket | Nobody |
  | Q | The ticket, then "Before you start, ask me anything you need to know." | Me, as the developer |
  | G | The ticket, then "Grill me on this before you build it." (`grilling` installed) | Me, as the developer |
  | GD | The ticket, then "Use grill-with-docs on this before you build it." | Me, as the developer |
  | GY | As G | A script: "Yes." to every round, then "Yes, go ahead." |

- **I played the developer.** Each ticket has a private brief (what the ticket leaves out, plus things I "don't
  mind"), written before any run. Fixed rules: answer only the question asked, "yes" to a recommendation that agrees
  with the brief, correct one that contradicts it, point to the repo for questions about the code, "your call" for
  things the brief doesn't care about. Every reply was labelled with the rule it followed, and a separate judge model
  checked every reply afterwards for anything I gave away that wasn't asked about.
- **Grading:** hidden tests, run after each session. The main score is **left-out requirements met**, counted only in
  runs that pass the ticket's own tests.
- **Stage 2:** each ticket on the Some and Lots levels has a follow-up ticket, done in a fresh session with no
  developer, starting from the plain app. 12 runs got the glossary and ADRs one grill-with-docs run wrote; 12 got
  nothing. Each follow-up leaves out one rule carried over from the first ticket (for example, the reason for
  reopening a case is a comment the customer can see, as the resolution was when it closed).
- **Statistics:** permutation tests stratified by ticket, Holm-adjusted across the four comparisons fixed in the
  design.

## 5. What happened

**Left-out requirements met, stage 1** (higher is better; counted only when the ticket's own tests passed):

| Arm | Clear tickets passed | Some: met / possible | Lots: met / possible | Requirements only in my head: met / possible |
| --- | --- | --- | --- | --- |
| T, ticket only | 6 of 6 | 5 / 12 | 14 / 24 | **0 / 15** |
| Q, "ask me anything first" | 6 of 6 | 6 / 12 | 15 / 24 | **0 / 15** |
| G, grilling | 6 of 6 | 12 / 12 | 24 / 24 | **15 / 15** |
| GD, grill-with-docs | 6 of 6 | 9 / 12 | 20 / 24 | **9 / 15** |
| GY, grilling, "yes" to all | 6 of 6 | 5 / 12 | 13 / 24 | **0 / 15** |

The requirements that were findable in the repository were met almost everywhere (17 or 18 of 18 in every arm).
All the difference is in the ones only the developer knew.

**The four confirmatory comparisons** (difference in requirements met per run; positive favours the first arm):

| Comparison | Difference | Holm-adjusted p | Result |
| --- | --- | --- | --- |
| H1: G − T, Lots tickets | +1.67 of 4 | 0.017 | Supported |
| H3a: G − GY, requirements only in my head | +1.25 | 0.0004 | Supported |
| H3b: GY − T, requirements only in my head | 0.00 | 1.0 | Supported (GY is no better than T) |
| H5: docs − no docs, stage 2 | +0.17 | 0.81 | No measurable difference |

**The developer's cost per run** (means; lower is cheaper for the developer):

| Arm | Level | Rounds answered | Questions asked | Words the developer read | Words the developer typed | Wrong recommendations I corrected |
| --- | --- | --- | --- | --- | --- | --- |
| G | Clear | 2.3 | 8.2 | 486 | 17 | 0.0 |
| G | Some | 2.7 | 9.2 | 614 | 55 | 1.0 |
| G | Lots | 2.5 | 10.7 | 704 | 85 | 1.8 |
| GD | Clear | 1.2 | 4.3 | 255 | 8 | 0.0 |
| GD | Some | 1.0 | 5.0 | 247 | 25 | 0.5 |
| GD | Lots | 1.0 | 4.8 | 272 | 40 | 1.0 |
| Q | any | 0 | 0 | 0 | 0 | 0 |

**The agent's cost per run** (means; lower is better): ticket only took about 1 minute and $0.013–0.019 at list
prices; grilling took 2.5–6 minutes and $0.025–0.030, roughly double the tokens. All 114 runs cost $2.52 in total.

**Stage 2** (higher is better):

| Follow-up | Docs: met / possible | No docs: met / possible | Carried-over rule met, docs / no docs | Docs that stated the carried rule | Docs runs that opened the docs |
| --- | --- | --- | --- | --- | --- |
| S1F | 3 / 6 | 3 / 6 | 0 / 0 | 0 of 3 | 1 of 3 (glossary only) |
| S2F | 3 / 6 | 3 / 6 | 0 / 0 | 3 of 3 (as the closing rule) | 0 of 3 |
| L1F | 5 / 6 | 3 / 6 | **2 / 0** | 2 of 3 | 3 of 3 |
| L2F | 6 / 9 | 6 / 9 | 0 / 0 | 1 of 3 (and 1 stated the opposite) | 0 of 3 |

The docs helped exactly where two things were both true: they contained the rule, and the next agent opened them. That
happened only on L1, where the ADR's file name (`0001-account-freeze-audit.md`) matched the follow-up's subject.

## 6. What surprised me

- **"Ask me anything first" produced no questions at all.** In 18 of 18 runs the agent said something like "I don't
  need any clarification" and built straight away, and it scored the same as ticket only. Permission to ask isn't
  enough; the skill is what makes it ask.
- **Saying "yes" to everything threw the whole gain away.** GY asked as many questions as G (8–9 per run), but every
  wrong recommendation was accepted, and it met 0 of 15 "in my head" requirements, the same as ticket only. In G
  runs I had to correct 1–2 recommendations per run on the Some and Lots tickets; those corrections are the whole
  gain.
- **Grill-with-docs often didn't wait for answers.** In 6 of its 18 runs it posted its questions and then built in
  the same turn ("I'll proceed with the recommended defaults"), so the developer never got to answer. That's why it
  scored below plain grilling. On S1, all three GD runs did this, and none met the "in my head" rule.
- **Grilling's recommendations were mostly right.** Most of what I typed was "Yes." The value was concentrated in one
  or two answers per ticket.
- **One ADR recorded the agent's guess as a decision.** A GD run that built without waiting wrote an ADR saying
  assignees are stored "without resolving" them, the opposite of the developer's rule. A later reader would take it as
  agreed.

## 7. What this might mean in practice

### Impact

Grilling works, and the reason is narrow: it creates a moment where the developer corrects one or two wrong
assumptions before code is written. On tickets that left out business rules, grilling met every one of them; ticket
only, "ask me anything" and "yes to everything" met none. On clear tickets it changed nothing and cost about 500 words
of reading and two to three times the wall time.

### Configuration recommendations

- **Use a grilling-style skill when the ticket depends on rules that live in people's heads** (who may do what, what
  the customer sees, what gets recorded). Skip it for tickets that spell everything out.
- **Don't rely on "ask me if you need anything".** With this agent it never asked.
- **Read the recommendations, don't rubber-stamp them.** The developer's job in a grilling session is to spot the one
  or two wrong recommendations. "Yes" to everything gives the same result as not being asked.
- **If you use grill-with-docs, tell it to stop and wait for your answers** (for example "ask, then wait for my
  reply before building"). Without that, a third of runs built before the developer could answer.
- **Make the docs findable.** Link `GLOSSARY.md` and `docs/adr/` from AGENTS.md (or the README) with a line saying
  to read them before changing the domain, and name ADRs after the rule, not the feature. In this run the next agent
  only opened an ADR whose file name matched its ticket.

### Risks this exposes

- **A false sense of having been consulted.** A grilling session where the developer says yes throughout looks
  thorough and produces the same result as no session.
- **Docs that record guesses as decisions.** When grill-with-docs builds without waiting, its ADRs record the agent's
  own assumptions as settled decisions. One did, and it contradicted the developer.
- **Docs that nobody reads.** Writing decisions down only helps if the next session opens them; most didn't.

## 8. What the experiment does not prove

- **The developer was me,** following a fixed brief, not a real person. A real developer forgets, knows more, gets
  tired of questions and sometimes says yes without reading. The audit shows I didn't give away more than was asked;
  it doesn't make the answers human.
- **One agent, one small repository, six tickets, three runs per cell.** The big effects (15 of 15 against 0 of 15)
  are clear; smaller ones (such as GD against G) are description, not tested.
- **The left-out requirements were written by me.** A fresh reader checked them for fairness before the run, but which
  ones I chose shapes the result.
- **Stage 2 started from the plain app, not from the first ticket's code** (as decided after the pilot). That
  isolates the docs but is less realistic: in real life the code would carry some of the rules.
- **The arms weren't fully blind.** The agents usually named their skill, so I could often tell which arm I was
  answering.

## 9. What I'd test next

- A real developer (or several) answering the same briefs, to see how often people say yes without reading.
- Grill-with-docs with an explicit "wait for my answers" line, to see if it then matches grilling.
- Stage 2 with an AGENTS.md line pointing at the glossary and ADRs.
- A larger repository, where more of the left-out rules are findable in code and asking matters less.

## 10. How to reproduce the results

```bash
cd 2026-10-grilling/scripts
./main.sh                       # T and GY, 36 runs
python3 -I relay.py setup       # 54 interview runs under anonymous IDs
python3 -I relay.py start <id>  # first turn; then reply with: relay.py reply <id> <file> '<labels json>'
python3 -I run.py grade <id>
./stage2.sh                     # 24 stage 2 runs (needs the interview key)
python3 -I audit.py <ids...>    # developer-reply audit (OpenRouter key needed)
python3 -I analyse.py           # tables and tests
```

Every developer reply and its labels are in `results/main/<run>/turns/`.

## Checks on the runs

See [results/checks.md](results/checks.md): every session ran `gpt-5.6-luna` at medium; no agent touched the hidden
tests or briefs; the audit found no leaks in 54 interviews; 9 turns stalled in Codex's `wait` call and were ended.

## 11. What changed from the design

All in the README's amendment log:

- Before the main run: stage 2 limited to the Some and Lots tickets; brief and test fixes after the fresh reader's
  check; stage 2 redesigned to start from the plain app (user's choice); L2 rd labelled guessable and left out of
  hypothesis 3 (user's choice).
- During the main run: a watchdog for turns that hang in Codex's `wait` call; the relay script; the blinding turned
  out weaker than planned.
- The design said stage 2 would have 18 docs runs; it had 12, as recorded before the run.
