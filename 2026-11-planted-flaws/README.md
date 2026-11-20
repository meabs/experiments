# Which kind of team finds the mistakes in a design? Nine agents review a draft with ten planted flaws (experiment PLF)

**Status:** design frozen 2026-11-20 after four pilots (amendment log) and before the main run. An
AI agent drafted this design from the owner's request. Later changes go in the amendment log (section 10). Follows
[2026-11-belbin-gke](../2026-11-belbin-gke/) (BLB) and [2026-11-belbin-cdc](../2026-11-belbin-cdc/) (BLC), whose checklist hit its
ceiling and could not say whether a design was right.

## 1. Question

A draft design for a highly available GKE platform with a Cloud SQL analytics feed contains **ten known flaws**. A team of
nine agents must review it and agree a version they are willing to put their names to.

1. **Which team leaves fewest flaws in the agreed document:** nine agents with the Belbin roles, nine sceptics, nine agreeable
   agents, or nine with no personality?
2. **Where is the gap:** in finding the flaws in discussion, or in actually fixing them in the document?
3. **What does it cost:** how many correct things do they wrongly "fix" or object to (false alarms)?

## 2. Why it is worth testing

In BLB and BLC agents agreed to version 1 quickly, nobody could say whether a design was right, and the coverage checklist
saturated. Here the draft is wrong in known, checkable ways, so the outcome is objective. Personality prompts are widely used
to make agent teams "diverse"; BLB found they barely showed. A temperament that is *about* checking (the sceptic) or *about*
trusting (the agreeable) is the test with the clearest expected effect, so if personality matters here it should show.

## 3. What is changed: the four conditions

Everything is the same except one paragraph in each agent's system prompt (the shared room rules, `arms/base.md`, come first):

| Condition | Paragraph added for all nine agents |
| --- | --- |
| NONE | nothing |
| BELBIN | each agent one of the nine Belbin roles (`arms/roles.json`, from [Belbin's page](https://www.belbin.com/about/belbin-team-roles)); the roles rotate across the letters from one repetition to the next |
| SCEPTIC | `arms/sceptic.md`: "You are sceptical by temperament. You do not take claims on trust: you assume a draft may contain mistakes until you have checked it ..." |
| AGREEABLE | `arms/agreeable.md`: "You are agreeable and supportive by temperament. You assume good faith and competence ... you value keeping the team's harmony and momentum over arguing about small matters." |

Held constant: nine agents A to I, `openai/gpt-5.6-luna` for all (OpenRouter, low reasoning effort, temperature 1.0), the task
(`arms/task.md`), the draft (`arms/draft.md`, loaded as version 1), one shared document with compare-and-swap edits, no
speaking order, no memory between sessions. The task does not say there are flaws or how many; it asks the team to confirm version 1 or amend it so the build can start (see the
amendment log for why it is a sign-off, not a review).

## 4. The draft and the flaws

`arms/draft.md` (about 850 words) is a design for a GKE platform with Cloud SQL (PostgreSQL) and change data capture into
BigQuery, written by "Agent I, the platform lead". **Agent I is in every condition** and has one extra paragraph
(`arms/author.md`): it wrote the draft, believes it is sound, defends its choices and gives way only to a clear argument or
evidence, not to repetition or pressure. So in every team one member has a stake in the draft; the other eight agents (and
Agent I's own condition paragraph) are what vary.

`flaws.json` lists **ten planted flaws**, each with the flawed statement, why it is wrong and what counts as fixed. They are
statements that are definitely wrong or inconsistent: (F1) a one-hour DNS TTL for a failover with a 15-minute RTO; (F2) three
services each budgeted at 99.95% "so the platform achieves 99.95%"; (F3) a PodDisruptionBudget of 6 of 6 replicas that "never
reduces capacity" (it blocks drains and upgrades); (F4) dashboards reading from the Cloud SQL high-availability standby (which
does not serve reads); (F5) a 15-minute BigQuery staleness limit against a 5-minute freshness target; (F6) Rapid called the
most stable release channel; (F7) a preferred pod anti-affinity said to "guarantee" separation; (F8) a restore that takes "five
minutes regardless of the size of the database"; (F9) six replicas at 800 requests a second said to "comfortably exceed" a
5,000 requests a second peak (6 x 800 = 4,800); (F10) a /22 pod range said to be enough for 30 nodes at 110 pods per node (GKE
reserves a /24 a node). The rest of the draft is meant to be correct.

**Pilot rule:** a short pilot first, not counted. If the NONE team finds at most 20% or at least 90% of the flaws in
discussion, the draft is too hard or too easy to separate conditions and I change it before the main run.

## 5. Measures

A blind coder reads each session's transcript (speakers anonymised, conditions not named), the original draft, the final agreed
document and `flaws.json`. All counts are per session out of 10.

1. **Remaining flaws (primary).** Flaws still present in the document the team agreed (the agreed version, or the last version
   if no agreement), by the `fixed_if` criteria. Lower is better.
2. **Found.** Flaws a team member said, in a message, were wrong (correctly), whether or not it reached the document.
3. **Fixed.** Flaws found and corrected in the agreed document. The **found-but-not-fixed gap** is Found minus Fixed.
4. **False alarms.** Distinct objections raised in the room that the coder judges to criticise correct text, and edits that
   introduce an error. Real defects in the draft that were not planted are counted separately as "other valid issues".
5. Process, from the event log: messages, document versions, rejected edits, whether and when all nine agreed (a team that
   approves version 1 straight away has zero found, ten remaining), cost.
6. **A second coder** (`anthropic/claude-haiku-5.5`) scores the same sessions for found, fixed and false alarms; agreement
   between the two coders is reported. A 12-session sample of the primary coder's flaw-by-flaw judgements is published for the
   owner to check by hand.

## 6. Hypotheses and analysis

Written before any run. Five sessions per condition is too few for confirmatory tests; every comparison is **exploratory**,
shown session by session with the condition mean and range.

- **H1.** SCEPTIC teams leave fewer flaws in the agreed document than NONE teams (a mean gap of at least 2 flaws). *Prediction: yes.*
- **H2.** AGREEABLE teams leave more flaws than NONE teams (a mean gap of at least 1). *Prediction: yes.*
- **H3.** BELBIN teams do not differ from NONE by 1 or more flaws. *Prediction: no difference.*
- **H4.** SCEPTIC teams raise more false alarms than NONE teams (at least 1 more per session on average). *Prediction: yes.*
- **H5.** The found-but-not-fixed gap is largest in AGREEABLE teams. *Prediction: yes.*

## 7. Size, cost and time

4 conditions x 5 repetitions = 20 sessions (session = (repetition - 1) x 4 + condition index + 1, interleaved so a partial run
is balanced), after the pilots (amendment log). A session has up to 120 messages and nine agents; earlier sessions of this kind cost
$0.07 to $0.32 at list price, so I expect about $3 to $6 in all, with the coders about $0.5. Ceiling **$10** in total, $1.20 a
session, enforced by the scheduler. Four sessions run at a time; about 5 to 10 minutes each.

## 8. Rounds

A second round could vary the number of flaws, use flaws that are harder to see than a wrong number, give agents a section each,
make approval conditional on closing every raised objection, or have a platform engineer review the agreed documents.

## 9. Limits known in advance

- One model, one document, one set of ten flaws, five sessions per cell: exploratory only. The flaws are in the domain the
  model knows well; a different domain may give a different answer.
- The flaws were chosen and written by an AI agent and not independently reviewed; each is checked against what I know of
  Google Cloud, and the owner should check the `truth` column. A flaw that the draft states in a way that is arguably not wrong
  would bias the results; the coders' judgements of "found" and "fixed" are one model's, with a second coder for agreement.
- The temperament paragraphs are two sentences. They test what the model does when told to be sceptical or agreeable.
- The draft may contain real defects I did not plant; those are counted separately and are not scored against teams.
- Compare-and-swap changes how agents edit; no memory across sessions.

## 10. Amendment log

| Date | Change | Before or after a measured run |
| --- | --- | --- |
| 2026-11-20 | First draft | Before |
| 2026-11-20 | **Pilot 1** (results/pilot1/; 8 flaws, no author): NONE found all 8 and fixed all 8, SCEPTIC found and fixed all 8 (the second coder returned nothing: Haiku spent its token budget on hidden reasoning; fixed by lowering its reasoning effort and raising the limit). Pilot rule: too easy | Before the main run |
| 2026-11-20 | **Pilot 2** (results/pilot2/; new draft of 8 more subtle flaws, still no author): NONE found 8 and 8, fixed 8 and 7; AGREEABLE found and fixed all 8. Nine reviewers asked to review catch textbook errors whatever their temperament. Pilot rule: still too easy | Before the main run |
| 2026-11-20 | **Changes made for the main run:** Agent I is the draft's author in every condition and defends it (`arms/author.md`); two cross-section flaws added (F9, F10), 10 flaws in all; the draft says it was written by Agent I. | Before the main run |
| 2026-11-20 | **Pilot 3** (results/pilot3/; the main design with the review framing, one NONE, one SCEPTIC, one AGREEABLE): all three teams still found 9 or 10 of 10 in discussion, but the final agreed documents left 1, 2 and 1 flaws, because fixes were wrong or incomplete (a /19 for 30 nodes, "seven or eight replicas" at 800 requests a second against a peak of 5,000), so the **remaining flaws** measure (the primary one) has spread while **found** is at its ceiling. Pilot rule: found is too easy to separate conditions, remaining is not; I proceed with remaining as the primary measure and report found as near ceiling. Three false alarms in the pilot, all by the coder's own judgement | Before the main run |
| 2026-11-20 | **Pilot 3, re-read:** re-running the coder with a reasoning budget (and a working second coder) changed the pilot's primary counts: NONE and SCEPTIC found 10 and fixed 10 (0 remaining), AGREEABLE found 9 and left 1; the earlier coder pass had wrongly marked a correct /19 as still wrong. All three teams are at the ceiling, so remaining flaws does not separate conditions either. Pilot rule: too easy | Before the main run |
| 2026-11-20 | **Task framing changed** (`arms/task.md`): from "review and agree a design you are willing to put your names to as correct" to "agree a design so that the build can start; confirm version 1 as it is, or amend it if you think it needs amending". The explicit review instruction made nine strong reviewers thorough whatever their temperament; a sign-off is the realistic situation in which temperament could matter. Neither text mentions flaws. | Before the main run |
| 2026-11-20 | **Pilot 4** (results/pilot/; the frozen main design: sign-off framing, author, 10 flaws; one NONE, one SCEPTIC, one AGREEABLE; both coders agree on the flaw counts): found in discussion NONE 7, SCEPTIC 10, AGREEABLE 8 of 10; left in the agreed document NONE 2, SCEPTIC 1, AGREEABLE 1; 62, 86 and 43 messages. NONE found 70%, inside the pilot rule's range, so the design is **frozen** and the main run starts | Before the main run |
