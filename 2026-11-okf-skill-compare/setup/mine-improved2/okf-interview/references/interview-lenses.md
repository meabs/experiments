# Interview lenses

Select prompts for the current knowledge gap; these are a menu, not a checklist to recite.

## Questions derived from code analysis
- This branch handles a case the tests do not explain. Which real situation requires it?
- This symbol and its documentation appear to disagree. Which behaviour is intended, and why?
- This value comes from configuration. Which external constraint determines the permitted values?
- This operation crosses a system boundary. Which guarantees hold after a timeout or partial completion?
- This module implements an unusual ordering or dependency. Which invariant must a change preserve?

Attach actual file/symbol/revision evidence to each selected question and inspect nearby code before asking. These prompts must not imply that an untested path is a bug. Questions that remain unanswered go into the engineer review log, not concept bodies.

## Opening and scope
- What do you look after, and which environment or customers does this apply to?
- What would someone misunderstand if they had only this repository?
- Tell me about a recent change or support case where context mattered.

## Domain meaning and business constraints
- Which terms mean something different here from their everyday meaning?
- What appears technically valid but is wrong for the business?
- Are there contractual, customer, regional, or historical exceptions?
- Which behaviour is intentional even though it looks like a bug?

## Decisions and tradeoffs
- Why this approach? What plausible alternative did you reject, and why?
- Is that an approved decision, your recommendation, or an inherited assumption?
- What must become true before we should reconsider it?
- Which apparently harmless refactor could violate that reasoning?

## Operations and support
- How do you distinguish normal waiting from a stuck job?
- What information do you gather before taking action? What confirms recovery?
- When is rerunning safe, and when should an operator stop?
- Which procedure depends on access or knowledge outside this repo?

## Dependencies, ownership, and coordination
- Which promises do upstream or downstream systems make, and where are they recorded?
- Who owns each side of the boundary? Which changes require coordination?
- Are there deployment windows, compatibility obligations, or ordering constraints?
- What is the actual escalation route? If unknown, who could establish it?

## Known issues and selective FMEA
- What can go wrong in this particular workflow? What have you actually observed?
- What triggers it, who is affected, and how can it be detected before harm?
- Is the proposed cause confirmed, or one explanation among several?
- What prevents it, what mitigates it, and what remains unprotected?
- What evidence would justify retrying, recovering, or escalating?

For a consequential failure, investigate mode → conditions/cause → effect → detection → controls → residual uncertainty. Keep unresolved parts in the review log; publish only independently complete answers that pass the admission gate. Use qualitative effects unless a real scoring method and sourced values exist. Do not invent likelihoods, severity scores, detection scores, RPNs, owners, or action deadlines. FMEA need not produce a separate concept or a table.

## Learning, freshness, and closure
- Is this still current? Which version, customer arrangement, or incident does it depend on?
- What evidence contradicts it? How would we find out it no longer applies?
- What should the next engineer check, and who could answer the remaining question?
- Here are the resulting claims and gaps. Which need correction?

Stop when the agreed scope has usable coverage, the engineer wants to stop, or remaining gaps need unavailable evidence. Record those gaps with actionable clarification requests in the separate review log. Publish only answers that pass the skill's completeness gate.
