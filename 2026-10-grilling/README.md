# Grill me first? Does being interviewed by the agent get you what you actually wanted?

**Final design, committed 2026-10-31 before any measured run.** Later changes go in the amendment log at the
bottom.

## Why

A ticket never says everything. The developer who wrote it knows things they didn't write down: the business rule
everyone "just knows", the convention the team agreed last month, the edge case that bit them before. A coding agent
that starts from the ticket can only guess at those.

Matt Pocock's [`grilling`](https://github.com/mattpocock/skills/tree/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/productivity/grilling)
skill (MIT) turns that around. Before building anything, the agent interviews the developer "relentlessly": it maps
the decisions as a design tree, asks every question it can ask now in numbered rounds, gives its own recommended
answer to each so that "yes" accepts it, looks facts up itself instead of asking, and doesn't start until the
developer agrees they understand each other. Its sibling,
[`grill-with-docs`](https://github.com/mattpocock/skills/tree/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/grill-with-docs),
runs the same interview plus [`domain-modeling`](https://github.com/mattpocock/skills/tree/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/domain-modeling),
which writes what was settled into the repository as it goes: a `GLOSSARY.md` of the domain's terms and short decision
records (ADRs) in `docs/adr/`.

The claim is attractive and easy to believe. It's also not free: every question costs the developer time, and an
agent that offers a recommended answer invites a busy developer to just say yes. This experiment measures what the
interview actually gets you, who it comes from (the developer's answers or the agent's own recommendations), and at
what point it's worth the developer's time.

Following the backlog rule, this isn't designed to show the simple approach wins. Most tasks have requirements the
ticket leaves out, which only an interview can recover, so grilling *should* win there. The question is by how much,
from where, and where the crossover is.

## Questions

1. Does grilling build more of what the developer actually wanted than working from the ticket alone?
2. Is the gain from the skill, or just from being allowed to ask? (Compare against a plain "ask me anything first".)
3. Is the gain from the developer's answers, or from the agent thinking it through and recommending answers? (Compare
   against a developer who says "yes" to every recommendation.)
4. Where does it become worth it? Tasks have 0, 2 or 4 requirements the ticket leaves out. How much developer time
   (questions read, words typed) does each extra requirement met cost?
5. Do grill-with-docs's glossary and decision records help a *later* ticket, done in a fresh session with no developer
   to ask? Do they cost anything on the first ticket?

## I play the developer

As in [egm-pilot](../2026-10-egm-pilot/), **Claude (the assistant running these experiments) acts as the human**,
answering the agent's questions at the level a working developer would. This is what makes 50-odd interviews
possible, and it's the experiment's main limit: a real developer brings more, and less, than a fixed brief.

Each task has a private **developer brief** (`tasks/<id>/developer.md`), written before any run and never shown to the
agent. It lists the requirements the ticket leaves out, each marked as either:

- **in the repo**: findable in the code or README (a convention, an existing helper, a pattern in neighbouring
  endpoints). A careful agent can find these without asking;
- **in my head**: a business rule or decision that exists nowhere in the repository. Only asking gets it.

Each brief also marks one requirement as **top of mind**, and lists a few decisions the developer **doesn't mind**
either way.

How the developer answers, fixed now and the same in every arm that has a developer:

- **Answer the question asked, briefly**, as a developer would in chat: one to three sentences, no lists of extra
  requirements, no requirements the question didn't touch.
- **A recommended answer that agrees with the brief, or that the brief has no view on:** "yes" (or "yes, fine").
- **A recommendation that contradicts the brief:** say no and give the brief's rule in plain words.
- **A question about a fact in the repository** (which the grilling skill says the agent should look up itself): point
  to where it is ("check how the other endpoints do it") without giving the answer. Counted separately.
- **An open question** ("anything else I should know?"): name the top-of-mind requirement if it hasn't come up yet;
  otherwise "no, that's it".
- **A question about something the brief has no view on:** "your call".
- **Cap:** after 6 rounds or 40 questions, "that's enough, go with your recommendations". Every time it's used is
  reported.

Every reply is saved with its run, and each sentence is labelled with the rule it follows (accept, correct from brief
item *n*, point to repo, top of mind, your call, cap). A script checks afterwards that no reply gave a brief item the
question didn't touch. I wrote the hidden tests, so this audit is the guard against me helping more than the brief
allows. I also don't know which arm a dialogue belongs to when I answer: the relay script shows only the agent's
message, and gives the grilling and ask-first sessions anonymous IDs. (The grilling format is recognisable, so this
blinding is partial; the audit is the real check.)

## Agent and repository

- **Agent:** Codex CLI 0.157.0 with hosted `gpt-5.6-luna`, reasoning effort `medium`, through AgentTrialRig 0.7.0, in
  the same bubblewrap sandbox as [repo-injection](../2026-10-repo-injection/) (hidden tests and briefs invisible). A
  dialogue is one Codex session: the first turn runs with `codex exec`, and each developer reply is sent with
  `codex exec resume <session>`. The session that asks the questions also builds the change, which is how the skill
  is meant to be used. Subagents (`--enable multi_agent_v2`) are on in every arm, because `grilling` asks the agent to
  send a subagent to look facts up.
- **Skills:** pinned to mattpocock/skills `4ae2317`, installed in the run's `.agents/skills/` only, with an otherwise
  empty Codex home (skills-impact found that home-folder skills leak into control arms). `grill-with-docs` can't be
  started by the model on its own (`disable-model-invocation: true`), so its arm's opening message names it, as a user
  would.
- **Repository:** sec-authz's accounts service ([`../2026-10-sec-authz/app/`](../2026-10-sec-authz/app/)), a
  multi-tenant Spring Boot 3.5 API with 25 tests, which Luna works on reliably and quickly. It has no GLOSSARY.md or
  ADRs to start with.

## Tasks

Six new ticket-style tasks on the accounts service, two at each level of what the ticket leaves out:

| Level | Tasks | Requirements left out of the ticket | Which of them are in the repo / in my head |
| --- | --- | --- | --- |
| Clear | C1, C2 | 0 | none |
| Some | S1, S2 | 2 | 1 / 1 |
| Lots | L1, L2 | 4 | 2 / 2 |

Tickets read like real ones: what's needed and why, the endpoint and its JSON fields, "follow the existing
conventions". The left-out requirements are the kind a reasonable developer would expect a colleague to ask about or
know: who may do it, what happens to related records, what counts as a duplicate, which money and time conventions
apply, what to log. None of them should be something a reasonable person would call a trick. Every brief is reviewed
against that test before any run, and any requirement that fails it is replaced.

**Grading** (hidden JUnit tests, run after the session, as in sec-authz):

- **Ticket tests:** what the ticket says, plus the existing 25 tests. A run must pass these to count as a working change.
- **Left-out requirement tests:** one group per left-out requirement. The main score is **left-out requirements met**:
  the number of groups passed, out of 0, 2 or 4, counted only in runs that pass the ticket tests (a broken change
  meets nothing).

## Arms (stage 1)

| Arm | Opening message | Developer |
| --- | --- | --- |
| **T** ticket only | The ticket | None: the agent works alone |
| **Q** ask first | The ticket, then "Before you start, ask me anything you need to know." | Me, by the rules above |
| **G** grilling | The ticket, then "Grill me on this before you build it." (`grilling` installed) | Me, by the rules above |
| **GD** grill-with-docs | The ticket, then "Use grill-with-docs on this before you build it." (`grill-with-docs` and its two skills installed) | Me, by the rules above |
| **GY** grilling, "yes" to everything | As G | A script that replies "yes" to every round, then "yes, go ahead" |

The arms pair up to answer the questions: T against G (question 1), Q against G (question 2), GY against G and T
(question 3), each across the three levels (question 4), and GD against G (cost on the first ticket).

**Runs:** 6 tasks × 5 arms × 3 runs = 90. 54 of them are interviews I answer (Q, G and GD).

## Stage 2: the next ticket (question 5)

Each task has a **follow-up ticket** in the same part of the domain, done later by someone else, in a fresh session,
with no developer to ask. Its own hidden tests include left-out requirements that the stage 1 interview could have
settled (for example, the same rule about who may see what), so a written record of the decisions would help.

To measure only the docs, not the code each run happened to write, every stage 2 run starts from **my reference
implementation of the stage 1 ticket**, plus:

- **docs:** the `GLOSSARY.md` and `docs/adr/` that one GD run wrote (each of the 18 GD runs gives one stage 2 run);
- **no docs:** nothing extra (18 runs, 3 per task).

Same agent and settings, ticket only, no skills. **Measure:** left-out requirements met on the follow-up ticket,
docs against no docs. I also record what the docs contain: how many brief items they state correctly, state wrongly,
or leave out, and whether they include anything I never said.

## Measures

- **Main:** left-out requirements met per run (as above); and whether the ticket tests passed.
- **Developer's cost:** rounds, questions asked, words the developer had to read, words the developer typed, and time
  to the first line of code. Also: questions about facts in the repo (the skill says not to ask these), recommended
  answers that were wrong and corrected, and wrong recommendations that a "yes" would have accepted.
- **Coverage:** for each left-out requirement, whether the dialogue asked about it at all, separately for "in the
  repo" and "in my head" items. This shows *why* a run missed something: never asked, asked but built wrong, or not
  needed because it was found in the code.
- **Agent's cost:** tokens (input, cached, output, reasoning), list-price cost and wall time per run.
- **Stage 2:** left-out requirements met; doc contents as above.

## Hypotheses (fixed before any run)

1. On the Lots tasks, G meets more left-out requirements than T.
2. G and Q: no direction predicted. If they come out level, the gain is from asking, not from the skill.
3. On the "in my head" requirements, G beats GY, and GY is no better than T: the gain comes from the developer's
   answers, not from the agent's recommendations.
4. On the Clear tasks, G is no better than T and costs more (tokens, time and developer words). The crossover, where
   grilling's extra requirements are worth its cost, is expected at Some or Lots.
5. In stage 2, docs meet more of the follow-up's left-out requirements than no docs.

## Analysis

Per arm and level: left-out requirements met as a proportion of those possible, with Wilson 95% intervals; ticket
pass rate. Comparisons for hypotheses 1, 3 and 5 use a permutation test stratified by task (10,000 permutations,
seed 1) on per-run counts, Holm-adjusted across the four confirmatory comparisons (G–T on Lots, G–GY and GY–T on
"in my head" items, stage 2 docs–no docs). Everything else is reported as description. With 3 runs per cell,
differences of a run or two mean nothing, and the report says "no measurable difference" when a test isn't significant.

## Before the runs

- **Pilot for the ceiling:** T on every task, 2 runs each. Clear tasks should pass; Some and Lots should pass the ticket
  tests and miss most "in my head" requirements. If T already meets the "in my head" requirements, the brief is leaking
  into the ticket or the repo, and the task is fixed before the main run.
- **Brief check:** a fresh reader (not me) is given each ticket and its brief and asked whether each left-out item is
  something a reasonable colleague would ask about or know. Any item marked unreasonable is replaced.
- **Developer dry run:** one G and one Q dialogue on a task that is not used in the main run, to check the reply rules
  work and that the audit script catches a leak I plant on purpose.
- **Isolation:** the hidden tests, briefs and references are invisible inside the sandbox (as in repo-injection).

## Limits, stated now

- **The developer is me, following a brief,** not a real person. A real developer is less consistent, may forget
  things, may know more, and gets tired of questions. The brief and the audit make my answers fair and repeatable; they
  don't make them human.
- **One agent, one repository, six tasks.** A small Spring Boot service with Luna at medium effort.
- **Left-out requirements are written by me.** The brief check is there to stop them being tricks, but which ones I
  chose shapes the result.
- **Stage 2 starts from my reference code,** so it measures the docs alone, not what a real team would have after
  stage 1.

## Amendment log

- 2026-10-31: design written at the user's request: "design an experiment that uses it, you act as the human and respond to the grill me questions at the level a developer would", "or this one which ever is best" (grill-with-docs). Both are used. The user approved the design ("Yes").
- 2026-10-31, while building, before any measured run (the pilot is not a measured run):
  - **Stage 2 covers only the Some and Lots tasks** (S1, S2, L1, L2). The Clear tasks settle nothing for docs to
    record. That makes 12 docs runs (one per GD run on those tasks) and 12 no-docs runs (3 per task).
  - **Codex 0.157's `exec resume` takes no `-s`**, so every turn sets the sandbox with `-c
    sandbox_mode="danger-full-access"` (the same setting). The developer sees every message the agent sent in a turn,
    not only the last one, because a round of questions can come before a closing line.
  - **The audit uses a judge model** (`openai/gpt-6-luna` through OpenRouter, `scripts/audit.py`) given the brief, the
    agent's message and my reply. In the dry run it found no leak in the two honest dialogues and caught both leaks I
    planted, after two fixes to its instructions: "touched" means the message raised the question that requirement
    settles (not just the same field), and an "open question" means an explicit "anything else?".
  - **Changes after the fresh reader's check** (a Claude subagent that had not written the tasks; its report is in
    `checks/brief-check.md`):
    - The L1 ticket says freezing is done "in the back office" (was "by staff in the back office"), and L2's says "This
      is done in the back office" (was "Admins do this in the back office"). The old wording pointed against L1 rc and
      L2 rd.
    - A starter overlay (`starter/`), laid on every workspace: notes 1, 4 and 5 in the fixtures are now written by an
      admin (support-written customer-visible notes contradicted S1 rb), and the two existing write endpoints now
      check the `accounts:write` scope that the README already requires (the code contradicted the README).
    - L1 rb is now "a closed account can't be frozen or unfrozen" (409). Unfreezing an open account moved to "don't
      mind", matching freezing a frozen one.
    - L1's follow-up drops its rule about skipping closed and frozen accounts: it was new, so no stage 1 interview
      could record it, and the README pointed the other way. The follow-up now has two left-out requirements.
    - S1's follow-up test for "support can't edit a customer-visible note" uses a note an admin wrote, not one the
      support user wrote.
    - Action endpoints whose status the ticket doesn't fix accept any 2xx.
    - Kept as a known counter-signal: fixture case k-2 is assigned to a support user who isn't assigned to its account
      (an existing test depends on it), which points against L2 rc.
    - The stage 1 references no longer offer the follow-ups a ready-made helper (L1's freeze-and-note method, L2's
      assignee check). Their rules are still visible in the reference code, so stage 2 measures what docs add on top
      of the code. That is said in the report, and the stage 2 pilot checks for a ceiling.
  - The first ticket-only pilot (before these changes) is kept in `results/superseded-pilot1/`. Second pilot: ticket
    only on every task and no docs on every follow-up, 2 runs each.
- 2026-10-31, after pilot 2, before any measured run. Pilot 2 (ticket only, 2 runs per task): Clear tasks 4 of 4
  passed; in Some and Lots, all 8 passed the ticket, "in the repo" requirements were met in 12 of 12 runs, and "in my
  head" requirements in 2 of 12, both L2 rd. Stage 2 with the stage 1 reference code: no docs met every left-out
  requirement on all four follow-ups (8 of 8 runs), a ceiling: the agent copies the rules from the stage 1 code. Two
  decisions put to the user:
  - **Stage 2 is redesigned** (user's choice, "Redesign: no stage-1 code"): follow-up runs start from the same app as
    stage 1 without the stage 1 feature's code, plus (docs arm) the GLOSSARY.md and docs/adr/ one GD run wrote. The
    carried-over rules are then only in the docs, if anywhere. This is less realistic (the follow-up comes before the
    feature it follows), and the report says so. The follow-up tickets were reworded so that they don't refer to
    stage 1's endpoints (they list the response fields, who may act, and what FROZEN means). Re-piloted with no docs,
    2 runs per follow-up: carried-over requirements met in 0 of 8 runs, "in the repo" ones in 8 of 8. The stage 1
    references are still used to check that the follow-up hidden tests are right. The earlier stage 2 pilot is kept in
    `results/superseded-stage2-pilot/`.
  - **L2 rd is relabelled "guessable"** (user's choice, "Keep, not in H3"): after L2's ticket stopped saying "Admins
    do this", the ticket-only agent met it in 2 of 2 runs. It stays in the main score but is left out of hypothesis 3,
    which compares requirements only the developer knows.
