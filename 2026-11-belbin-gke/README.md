# Does giving a team of AI agents Belbin team-role personalities change the design they write? A highly available GKE cluster (experiment BLB)

**Status:** design frozen 2026-11-20, main run started. An AI agent drafted this design; the owner asked for the
experiment and has not yet reviewed it. Later changes go in the amendment log (section 10).

## 1. Question

Nine agents share a chat room and write one design document together: a highly available Google Kubernetes Engine (GKE)
cluster platform. In one condition each agent is given one of the nine [Belbin team roles](https://www.belbin.com/about/belbin-team-roles)
as its personality, in its system prompt only. In the other, all nine have the same prompt with no role.

1. **Do the personalities show?** Can a reader who is not told the roles tell which role an agent was given from its
   messages?
2. **Does it change how the team works?** Talk, challenge, edits, how long it takes to agree.
3. **Does it change the document?** Coverage and specificity of the design, against a checklist fixed beforehand.

## 2. Why it is worth testing

Personas are a common way to make multi-agent teams "diverse". The earlier [emergent-room](../2026-11-emergent-room/)
experiment found that differences between agents were the model's, and that agents with no assigned role were mostly
alike and agreeable. It did not test assigned roles. A well-known human framework with published descriptions is a fair
test of whether prompting for roles changes behaviour or only tone.

## 3. What is changed: the two conditions

| Condition | System prompt |
| --- | --- |
| BELBIN | the shared room instructions (`arms/base.md`) plus one paragraph per agent (`arms/roles.json`) built from the Belbin page: the role, its short description, its strengths and its allowable weaknesses, in Belbin's wording, ending "Work as yourself in this role. You are not told what to say, and you are not told the other members' roles." |
| CONTROL | the same shared room instructions, no role paragraph |

Held constant: nine agents (A to I), `openai/gpt-5.6-luna` for every agent, through OpenRouter, reasoning effort low,
temperature 1.0; the task text (`arms/task.md`); the shared document; no memory between sessions; no speaking order.
Personalities are only text in the system prompt: nothing scripts who speaks or what they say. In the second repetition
the roles are assigned to letters in reverse order, so a letter is not tied to a role.

## 4. The task and the room

The task (`arms/task.md`) asks for a detailed design for a highly available GKE platform for a customer-facing web
application (stateless web and API tier, a relational database, a message queue), 99.95% monthly availability, about
5,000 requests a second at peak, one continent, a team of eight engineers, surviving the loss of a zone unattended and
having a rehearsed recovery for a region. It lists the topics the document must cover but not what to say about them.

One shared document, shown at every turn. `DOC:` replaces it, but only if the agent's edit was based on the current
version: otherwise the edit is rejected and the room is told (compare-and-swap; the earlier experiment's agents
overwrote each other). `AGREE vN` approves a version. The session ends when all nine have agreed to the same version,
at 150 messages, at a $2 budget, or when the room goes quiet. An agent is asked again when two new messages exist, or when
nothing else is running.

## 5. Measures

1. **Role recognisability.** A blind coder (`openai/gpt-6-luna`, a different model from the agents) is given 12 of an
   agent's messages with names removed and the nine Belbin role descriptions, and picks the best-fitting role. Accuracy
   against chance (1 in 9). The same procedure runs on CONTROL agents, which have no role, to show what a guess looks like
   when there is nothing to find.
2. **Process** (counted from the event log): messages, share of messages that challenge (coder), document versions,
   rejected edits, who posted the document, messages until all agree, whether they did.
3. **Document quality, coverage.** A blind coder scores the agreed version (or the last version) against a 12-item
   checklist, fixed here, 0 (absent), 1 (mentioned generically), 2 (specific: names the mechanism and setting):
   1. regional control plane and the cluster topology across zones;
   2. node pools across at least three zones, autoscaling and headroom for the loss of a zone;
   3. workload placement: replicas, topology spread or anti-affinity, disruption budgets;
   4. what happens in a zone failure, how recovery happens without a person;
   5. region failure: disaster-recovery design with a stated recovery time and recovery point objective;
   6. the stateful tier: how the database is made highly available, replication, backups and tested restores;
   7. traffic entry: load balancing, health checks, connection draining;
   8. upgrades and maintenance: channels, windows, surge, rollback, interaction with disruption budgets;
   9. networking: VPC design, private access, egress, address capacity;
   10. observability: SLIs, SLOs, error budget, alerts;
   11. security that affects availability (identity, policy, supply chain, quotas);
   12. risks, assumptions and trade-offs stated, and a plan to test failures.
   Total 0 to 24, plus word count. This measures coverage and specificity, **not technical correctness**. The coder is also
   asked to list claims that look wrong; those are for the owner to review and are not scored.
4. Cost and tokens per session from the API's usage fields at list price ($0.20 in, $1.20 out per million).

## 6. Hypotheses and analysis

Written before any run. Two repetitions per condition give no sample for confirmatory tests: every comparison is
**exploratory** and reported as counts and ranges, with the individual sessions shown.

- **H1.** Belbin agents are recognisable: the coder names the assigned role for at least a third of them (chance is
  1 in 9, 11%), while control agents' guesses are no better than chance. *Prediction: yes.*
- **H2.** Belbin rooms do not write a more complete design than control rooms: the checklist totals differ by 3 points or
  fewer out of 24. *Prediction: yes, no gain.*
- **H3.** Belbin rooms challenge more and take more messages to agree than control rooms. *Prediction: yes.*

## 7. Size, cost and time

4 sessions (BELBIN, CONTROL, BELBIN reversed, CONTROL), after one 30-message pilot of the BELBIN condition that is not
counted. Each session up to 150 messages, nine agents, a document of about 1,000 words in every prompt. Estimate from the
pilot goes in the amendment log. Ceiling **$8** in total, $2 a session, enforced by the scheduler. The owner's OpenRouter
balance pays for it. About 20 to 40 minutes a session.

## 8. Rounds

A second round could swap the model (Claude Haiku 5.5, which challenged more in EMR), use fewer or hand-picked roles, or
have a human platform engineer review the documents for technical correctness.

## 9. Limits known in advance

- Four sessions, two per condition, one model: exploratory only.
- The checklist measures coverage, not correctness; a confident wrong design scores well. The owner should review the
  documents and the flagged claims.
- Belbin's roles are a human framework and the page says people can play more than one role; a prompt paragraph is a
  thin version of that.
- The coder is another model and not hand-checked; a sample is published for checking.
- The checklist and the task were written by an AI agent and the owner has not independently reviewed them.
- Parallel turns mean many messages are written before newer ones land; edits are protected by compare-and-swap but
  discussion is not.

## 10. Amendment log

| Date | Change | Before or after a measured run |
| --- | --- | --- |
| 2026-11-20 | First draft | Before |
| 2026-11-20 | Pilot (BELBIN, 30-message cap, results/pilot/): worked; 36 messages, 2 document versions, 6 rejected edits, $0.065, so I expect $0.3 to $0.8 a session and about $2 in all. Not counted. Observed: after version 1 many agents sent near-identical requests to revise the same paragraph and nobody edited. No change to the design | Before the main run |
| 2026-11-20 | Main run finished: 4 sessions, all ended with all nine agents agreeing (versions 1, 1, 2, 1), $0.42 at list price. | After the run |
| 2026-11-20 | Analysis change: agents say only about four substantive things per session (many messages are `AGREE`), so the planned "12 messages per agent" for role recognition is impossible; the coder now gets every substantive message (over 60 characters, not an `AGREE` line) of each agent that has at least 2. The first pass of the script used 4 and covered only 4 agents; it is not reported | After the run |
| 2026-11-20 | The first scoring call for session 1's checklist returned nothing (output limit); rerun with a larger limit | After the run |
