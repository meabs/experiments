# Which kind of team finds the mistakes in a design? Nine agents review a draft with eight planted flaws (experiment PLF)

**Status:** design frozen 2026-11-20 before any run of this experiment (a pilot is allowed by the pilot rule, section 4). An
AI agent drafted this design from the owner's request. Later changes go in the amendment log (section 10). Follows
[2026-11-belbin-gke](../2026-11-belbin-gke/) (BLB) and [2026-11-belbin-cdc](../2026-11-belbin-cdc/) (BLC), whose checklist hit its
ceiling and could not say whether a design was right.

## 1. Question

A draft design for a highly available GKE platform with a Cloud SQL analytics feed contains **eight known flaws**. A team of
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
speaking order, no memory between sessions. The task does not say there are flaws or how many; it says that approving a
version means being willing to put your name to it as correct.

## 4. The draft and the flaws

`arms/draft.md` (553 words) is a design for a GKE platform with Cloud SQL (PostgreSQL) and change data capture into BigQuery.
`flaws.json` lists **eight planted flaws**, each with the flawed statement, why it is wrong, and what counts as fixed. They are
statements about Google Cloud behaviour or arithmetic that are definitely wrong: (F1) a zonal cluster's control plane
"survives the loss of a zone"; (F2) three zones each at 80% utilisation "absorb" the loss of one; (F3) a PodDisruptionBudget
"guarantees" replicas through a zone failure; (F4) Cloud SQL high availability "fails over automatically" to another region;
(F5) asynchronous replication "gives an RPO of zero"; (F6) a regional load balancer has "a single anycast IP serving both
regions"; (F7) BigQuery "enforces the primary key" so no de-duplication is needed; (F8) 99.95% a month "allows about 4.4
hours of downtime" (it is about 22 minutes; 4.4 hours is the yearly figure). The rest of the draft is meant to be correct.

**Pilot rule:** one NONE and one SCEPTIC session first, not counted. If the NONE pilot finds at most 1 or at least 7 of the 8
flaws in discussion, the draft is too hard or too easy to separate conditions, and I rewrite the flaws before the main run.

## 5. Measures

A blind coder reads each session's transcript (speakers anonymised, conditions not named), the original draft, the final agreed
document and `flaws.json`. All counts are per session out of 8.

1. **Remaining flaws (primary).** Flaws still present in the document the team agreed (the agreed version, or the last version
   if no agreement), by the `fixed_if` criteria. Lower is better.
2. **Found.** Flaws a team member said, in a message, were wrong (correctly), whether or not it reached the document.
3. **Fixed.** Flaws found and corrected in the agreed document. The **found-but-not-fixed gap** is Found minus Fixed.
4. **False alarms.** Distinct objections raised in the room that the coder judges to criticise correct text, and edits that
   introduce an error. Real defects in the draft that were not planted are counted separately as "other valid issues".
5. Process, from the event log: messages, document versions, rejected edits, whether and when all nine agreed (a team that
   approves version 1 straight away has zero found, eight remaining), cost.
6. **A second coder** (`anthropic/claude-haiku-5.5`) scores the same sessions for found, fixed and false alarms; agreement
   between the two coders is reported. A 12-session sample of the primary coder's flaw-by-flaw judgements is published for the
   owner to check by hand.

## 6. Hypotheses and analysis

Written before any run. Five sessions per condition is too few for confirmatory tests; every comparison is **exploratory**,
shown session by session with the condition mean and range.

- **H1.** SCEPTIC teams leave fewer flaws in the agreed document than NONE teams (a mean gap of at least 2). *Prediction: yes.*
- **H2.** AGREEABLE teams leave more flaws than NONE teams (a mean gap of at least 1). *Prediction: yes.*
- **H3.** BELBIN teams do not differ from NONE by 1 or more flaws. *Prediction: no difference.*
- **H4.** SCEPTIC teams raise more false alarms than NONE teams (at least 1 more per session on average). *Prediction: yes.*
- **H5.** The found-but-not-fixed gap is largest in AGREEABLE teams. *Prediction: yes.*

## 7. Size, cost and time

4 conditions x 5 repetitions = 20 sessions (session = (repetition - 1) x 4 + condition index + 1, interleaved so a partial run
is balanced), after a 2-session pilot. A session has up to 120 messages and nine agents; earlier sessions of this kind cost
$0.07 to $0.32 at list price, so I expect about $3 to $6 in all, with the coders about $0.5. Ceiling **$10** in total, $1.20 a
session, enforced by the scheduler. Four sessions run at a time; about 5 to 10 minutes each.

## 8. Rounds

A second round could vary the number of flaws, use flaws that are harder to see than a wrong number, give agents a section each,
make approval conditional on closing every raised objection, or have a platform engineer review the agreed documents.

## 9. Limits known in advance

- One model, one document, one set of eight flaws, five sessions per cell: exploratory only. The flaws are in the domain the
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
