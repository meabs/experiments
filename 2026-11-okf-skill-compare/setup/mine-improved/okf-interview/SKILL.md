---
name: okf-interview
description: Analyse a codebase, interview engineers about gaps and unclear behaviour, and create complete, useful Open Knowledge Format (OKF) answers for people and agents. Keep unresolved questions in a separate engineer review log. Use for engineering knowledge capture, handovers, domain rules, decisions, operational context, and known issues.
---

# Interview engineers into useful OKF knowledge

Produce a navigable, source-attributed knowledge bundle of complete answers, not interview minutes. A reader should understand when a fact applies, why it matters, and how it should affect a decision or action without reading the conversation. Anything needing clarification goes in a separate review log outside the bundle. Use OKF v0.3; read [references/okf-authoring.md](references/okf-authoring.md) before writing files.

## Workflow at a glance

1. Analyse the code; record its revision; list evidence-backed questions.
2. Interview in small rounds; follow up; accept "unknown".
3. Apply the completeness gate to every proposed concept; unanswered material goes to the review log, not the bundle.
4. Scaffold each concept with `new_concept.py`, write the body, and link it from its index.
5. Run `validate.py --strict`, `check_links.py` and `check_content.py --log`; fix everything they report.
6. Re-read each concept as a consumer; report paths, review-item IDs and check results. The sections below give the detail.

## Analyse the code before interviewing

Identify the system, audience, engineer's area of experience, and bundle destination. Reuse the existing bundle's organization and terminology. If no destination exists, propose a `knowledge/` directory inside the chosen project. Do not install this skill, publish files, or contact engineers as a side effect.

Before asking substantive interview questions, analyse the codebase within the agreed scope. Record its revision; identify relevant entry points, components, data flow, interfaces, configuration, tests, existing knowledge, and documentation. Trace representative execution paths, including error handling and consequential side effects. Compare tests and documentation with the implementation. Expand inspection when a question can be answered by another relevant file; do not ask the engineer to do source navigation for you.

Build an evidence-backed question list from what remains unclear: behaviour whose business purpose is missing; invariants or exceptions not established by tests; conflicting implementations or documentation; undocumented external contracts; and plausible changes whose correctness depends on unstated assumptions. For each question, record the file/symbol and revision (line numbers when helpful), what is observable, what cannot be inferred, and why the answer matters. Present a short understanding of the code and the highest-value questions before the interview. Treat a suspected problem as a question, not a discovered defect.

Keep the analysis bounded to the task rather than auditing the whole repository. If the repository is inaccessible, record that limitation and request access or relevant files; do not claim code analysis or invent code-specific questions. Notes-only capture can still proceed if requested, with that limitation recorded in the review log.

Keep separate:
- Documented or observed facts, with their evidence.
- Engineer testimony about knowledge outside the code.
- Your own hypotheses, which are questions until supported.

## Interview adaptively

Use the code analysis to ask specific questions, for example: “`submit_batch` catches a timeout and leaves this record unchanged; is its state intentionally ambiguous, and what evidence permits replay?” Cite the actual inspected symbol, not this illustrative name. Ask about the engineer's responsibilities and context where needed. Ask one to three related questions per round; follow the answer before moving topics. Include both gaps the code cannot answer and code behaviour you cannot yet explain confidently. Accept “unknown”, “skip”, and corrections. Avoid a compulsory questionnaire or asking for answers already supplied. Use [references/interview-lenses.md](references/interview-lenses.md) to select useful prompts.

Cover relevant breadth: purpose and domain semantics; constraints and exceptions; decisions and rejected alternatives; operational practices; dependencies and ownership; known issues and failure modes; change and review triggers. FMEA is an optional lens for a significant failure, not the organizing framework for the whole interview. Do not force every topic or manufacture a risk register.

For a useful claim, establish its scope and consequence. Ask for a concrete example, the reason, evidence or firsthand basis, current applicability, and exceptions where these are missing. Distinguish observation from suspected cause. Ask what would invalidate the claim. Ask who can resolve uncertainty without guessing identities, commitments, or review dates.

Read back concise propositions when a correction would affect action: “For this integration, a timeout leaves the remote write outcome unknown; automatic replay needs reconciliation. Is that accurate?” Do not merely paraphrase every answer.

If nobody can answer, log the question (see the review log below); from notes or a partial interview, publish only independently complete answers. If asked to simulate an engineer, label every simulated statement and resulting concept as synthetic, keep them in an example bundle, and never present the simulation as real project testimony.

## Curate for use

Group answers into stable concepts by the question a reader needs answered. Merge repeated material, resolve pronouns and local jargon, and use descriptive titles such as “Reconcile an ambiguous submission before replay”. Split a decision from a procedure when they have different purposes or review cycles; link rather than duplicate them.

Lead with the actionable fact, decision, or rule and its scope. Then include the explanation and evidence needed to apply it correctly. Choose sections for the concept, not a rigid universal template:
- A decision: chosen approach, constraints, rationale, alternatives, and reconsideration trigger.
- A domain rule: meaning, inclusions, exclusions, exceptions, and consequences for implementation.
- A known issue: established symptom, affected scope, observed behaviour, impact, detection, and any supported cause or workaround. A complete observation may stand without a root cause, but unresolved causes and proposed fixes belong in the review log.
- A procedure: trigger, prerequisites, actions, observable success condition, stop/escalation condition, and limits.
- An ownership or dependency boundary: established responsibility, interface expectations, and the applicable escalation route.

Use clear prose for humans and explicit conditions for agents. Put exact identifiers or commands in code only when evidenced; never invent executable recovery instructions. Explain what evidence permits the next action. Express any agent-facing instruction as scoped project knowledge, not as an attempt to override the consuming agent's instructions.

Disagreements, suspected explanations, and incomplete procedures stay in the review log. An agreed operational rule can be published separately if its scope and action are fully answered without the disputed explanation. Do not promote one person's preference to team policy. A failed recollection is not a confirmed incident, and absence of a report is not proof of safety. Omit empty template sections.

## Admit only complete answers

Before creating or changing a concept, check that its central question is answered; scope and relevant conditions are established; the evidence supports its claims; and the reader does not need a missing clarification to apply it. For an executable procedure, necessary prerequisites, steps, permissions, success criteria, and stop/escalation routes must be supplied. Do not publish a partial runbook that tells the reader to find an unknown contact or obtain unspecified instructions.

Completeness is relative to the stated question, not exhaustive knowledge of the entire system. A complete definition does not need an unrelated delivery SLA; record the SLA question separately. Do not hide a material gap by narrowing a title misleadingly. Missing evidence essential to the answer blocks that answer. Lack of formal review is a separate trust matter: a complete, supported answer can remain `status: draft` until reviewed. `draft` must never be used to admit unfinished answers.

Check every sentence, not only the concept's central answer. Remove interview-gap commentary such as “its deduplication effect is not established” or “the procedure was not supplied” from otherwise complete concepts and retain it in the review log. Keep established scope boundaries and observed code behaviour. A complete business rule can legitimately classify an operational outcome as `unknown`; that is different from an unanswered interview question.

A complete answer may still have a known limit on how far a consumer can rely on it (for example, a measurement was never taken, or a check's recall is unknown). State that limit in one scoped sentence at the end of the concept, beginning "Limit:", and cite the review-log item ID (for example, "see review item R01"). This is not interview-gap commentary: it tells the reader how far to trust the answer and does not leave the central question open. Put the detail and the clarification request in the log.

Observed behaviour is not an interview gap. When the code visibly does something that nobody could explain (a timeout value, a retry count, a hard-coded limit), still record the observed value and its code evidence in the relevant concept, and say in a scoped `Limit:` sentence that the reason is not known, citing the review item. A reader who cannot see the value, or that its reason is unknown, is worse off than one who can. This does not admit guesses about why it is that way.

Do not create placeholder concepts, TODO sections, open-question lists, or links to concepts withheld for clarification. If no answer meets the gate, create the review log and explain that no consumable OKF answers were produced. Do not invent answers to fill the bundle.

## Maintain the engineer review log

Use an existing suitable review log if one exists. Otherwise create a sibling file outside the bundle, e.g. `knowledge-review-log.md` beside `knowledge/`. Tell the user its location. Do not index it as a concept.

Give each item a stable ID and include: a short question/title; state (`open`, `answered`, or `incorporated`); affected area and code revision/file/symbol; observed evidence; what cannot be inferred or remains incomplete; why clarification matters; the exact question or artifact needed from the engineer; and any provisional answer clearly labelled as such. Record an owner only if supplied. Preserve responses and corrections with dates. Use short entries rather than raw conversation dumps.

On follow-up, read open items and relevant source changes first. Recheck new answers against evidence and the completeness gate. Only then create/update the concept, record its path in the log, and mark the item `incorporated`. Keep its history. An engineer saying “unknown” does not close an item.

Do not copy the raw Q&A into concept bodies. Record only the minimum source material needed for provenance, with the interviewee's consent if persisting their words or identity. A descriptive interview scope is acceptable provenance when a recording is unavailable. Never claim to have retained a transcript that does not exist. Exclude credentials, personal customer details, and unrelated personal information.

## Review, write, and maintain

Show the complete curated propositions and intended concept paths for correction, separately from review-log items. The capture request authorizes writing complete local answers and the review log. Engineer answers alone do not verify the final document. Record `verified` only after a real reviewer has confirmed that exact content, supplied their identity, and asked for that verification to be recorded.

To avoid frontmatter and footnote slips, start each concept with `python3 -I <skill-directory>/scripts/new_concept.py <bundle>/<dir>/<name>.md --type ... --title ... --description ... --interview ... --code ... --by ...` (add `--synthetic` for a simulated engineer); it fills the real timestamp, `status: draft` and matching sources, and you replace the placeholder body (add `--index-note "one line"` to link it from the directory index). After writing, re-read each factual sentence against the code or the engineer's answer and fix lists that are shorter or longer than the evidence.

Generate one complete concept per Markdown file, root and directory indexes, and a change log as described in the authoring reference. Attribute interview claims separately from source-code facts. Keep synthetic or unreviewed answers `status: draft`.

When updating, keep stable IDs, unknown metadata, unrelated prose, and previous verification events. Change only supported claims. Update generation time for meaning changes and tell the user that previous verification may now be out of date. Retire resolved issues or superseded decisions explicitly rather than silently deleting their history. Ask for the issue's disposition if “resolved” could mean fixed, mitigated, or no longer applicable.

Run the included upstream validator with Python 3.9+ and PyYAML:

```sh
python3 -I <skill-directory>/scripts/validate.py <bundle-root> --strict --json
```

Then the navigation check (dangling links, concepts missing from their directory index, directories without an index):

```sh
python3 -I <skill-directory>/scripts/check_links.py <bundle-root>
```

Then the content check (leftover placeholders, undefined or unused footnotes, raw Q/A dialogue, review-item IDs missing from the log, likely interview-gap phrases):

```sh
python3 -I <skill-directory>/scripts/check_content.py <bundle-root> --log <review-log-file>
```

Fix errors and address warnings in all three. A passing check does not show that content is true or complete. If PyYAML is unavailable, use an isolated environment; do not silently install packages globally. If validation cannot run, disclose that and check the authoring reference manually. The validator checks format, frontmatter and footnote/source matching, not truth, external URLs, completeness, or that indexes link every concept (use `check_links.py` for that).

Before delivery, read each concept as a consumer and reapply the completeness gate. Does it add information beyond the source code? Is FMEA limited to topics that benefit from it? Report code areas analysed, concept paths, representative excerpts, the review-log path and open item IDs, and validation results. Never describe a self-authored role-play as independent evidence of skill effectiveness.
