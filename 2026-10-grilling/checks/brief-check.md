# Brief check: fresh reader's report (2026-10-31, before any measured run)

The reader was a Claude subagent with no part in writing the tasks. It was asked to read every ticket, brief, follow-up
and hidden test plus the repository, and to judge whether each left-out requirement is reasonable, correctly labelled
("in the repo" or "in my head"), not contradicted by the ticket, and fairly tested. It edited nothing. Its report is
below as it gave it. What was changed in response is in the README's amendment log (2026-10-31).

## Structural issues

**A. Stage 2's carried rules are already in the code.** `run.py` lays `reference/base` and the stage 1 reference over
the workspace for both the docs and no-docs runs, so the no-docs agent can read every carried rule: in
`AccountNoteController` ("Only admins can add notes the customer can see"), `CaseCloseController` (the resolution saved
as `CaseComment(..., false)`), `AccountFreezeController.freeze(account, reason, by)` (a public helper that writes the
note; reusing it meets L1F ra for free) and `CaseAssigneeController.checkAssignable`; and
`@PreAuthorize(SCOPE_accounts:write)` is on every reference endpoint. So every carried item is in practice "in the
repo" in stage 2, and hypothesis 5 is likely to hit a ceiling. The exception is S1F ra's "can't edit a
customer-visible note", which the code only covers for adding notes.

**B. L1F rb is a new "in my head" rule with no developer to ask.** Neither arm can get it: the stage 1 brief never
mentions bulk behaviour, so docs can't contain it. It is pure noise, and the starting code points the other way (the
L1 reference answers 409 for any account that isn't open, and the README says a change request is "refused as a
whole").

**C. The write scope is stated in the README but not enforced by any existing code.** The existing `POST
/api/accounts/{id}/closure-requests` and `POST /api/cases` have no `accounts:write` check, so an agent copying
neighbouring endpoints will miss it. "In the repo" is still correct, but the code is a counter-signal. S1 and S2 also
need the scope but don't test it: fine, but inconsistent with L1 and L2.

## Per task

**C1.** Clear: yes. Ticket tests match the ticket exactly. (`LocalDate.parse` throws `DateTimeParseException`, which
the handler doesn't map, so it gives 500: the agent's problem, not unfairness.)

**C2.** Clear: yes. Ticket tests match. Minor: `contains(1, 2)` for SAM fixes an order that comes from `findAllById`,
but "behaves exactly as now" covers it.

**S1.** ra (customer 403; unassigned support or other bank 404): reasonable, label correct, fair. rb (support may only
add internal notes): borderline-yes, label correct; **fixtures** notes 1, 4 and 5 were written by support users with
`internal = FALSE`, which implies support writes customer-visible notes.

**S1F.** ra (carried): yes for "make visible", borderline for "edit a visible one"; **the test has SAM edit note 1,
which SAM wrote**, and "an author can edit their own note" is a natural reading. rb: fair.

**S2.** ra (closing a closed case is 409, no second comment): yes, correct. rb (resolution as a customer-visible
comment by the closer): yes; the ticket asks for a resolution with nowhere to store it. Ticket tests fine; `isOk()` on a
POST whose status the ticket doesn't fix is low risk.

**S2F.** ra (carried): visible in the S2 reference code (see A). rb (reopening an open case is 409): fair.

**L1.** ra (write scope): fair, but see C. rb (freeze closed 409; unfreeze not-frozen 409): yes for closed; borderline
for unfreezing an open account; **inconsistent with the brief**, which lists freezing an already-frozen account as
"don't mind". rc (support can freeze, only admins unfreeze): plausible; mild contradiction, since "Freezing and
unfreezing are done by staff" makes "staff can do both" the obvious reading. rd (internal audit note): yes; mild hints
in the `AccountNote` javadoc and fixture note 2.

**L1F.** ra (carried): effectively in the repo (A). rb: correct as a business rule but unreachable in stage 2 (B), and
the README and the L1 reference point the other way. rc (scope): fair.

**L2.** ra, rb: fair. rc (assignee must be assigned to the account, else 400): borderline label, since
`support_assignments` is the only list of support users; **fixture** k-2 is assigned to u-sue, who isn't assigned to
account 1, a live counter-example (and the `SupportCase` javadoc stresses the two differ). rd (current assignee can
hand over): **strong contradiction**: "Admins do this in the back office; customers can't" makes admin-only the obvious
reading.

**L2F.** ra (carried): in the repo in stage 2 (A). rb (unknown or other-bank case is 404): fair; minor overlap with ra
in the test data (u-sam isn't assigned to account 4), low risk because checking visibility first is natural. rc
(scope): fair.

## Recommendations

1. L2 ticket: "This is done in the back office; customers can't."
2. L1 ticket: "Freezing and unfreezing are done in the back office; customers can't do either." (or accept as mild)
3. L1 rb: make it consistent (drop the unfreeze-an-open-account assertion, or make freezing a frozen account part of rb).
4. S1F `ra_supportCannotEditCustomerVisibleNote`: use note 3 (written by u-ada, public).
5. Fixtures contradicting S1 rb (notes 1, 4, 5): overlay a `data.sql` with author u-ada, or document as a counter-signal.
6. Fixture contradicting L2 rc (k-2): can't change it (an existing test depends on it); note it, and watch whether the
   pilot meets rc anyway.
7. Write scope: add the scope check to the two existing write endpoints in an overlay, or report the inconsistency.
8. Stage 2: relabel carried items as "in the repo (stage 1 code)" and narrow hypothesis 5 to what docs add beyond the
   code, or redesign follow-ups to need the rule's reason; pilot stage 2 for a ceiling.
9. L1F rb: drop from scoring, report separately, or add bulk behaviour to the L1 brief.
10. Optional: for POST action endpoints whose status the ticket doesn't fix, state 200 in the ticket or accept any 2xx.

## What was done

1, 2, 3 (dropped the unfreeze-an-open-account assertion; both moved to "don't mind"), 4, 5 (overlay), 7 (overlay),
9 (dropped), 10 (any 2xx). 6: noted; the pilots met L2 rc in 0 of 2 runs before the change. 8: the shared helpers
were removed from the references, the carried rules stay visible in the code, hypothesis 5 is read as "what docs add
on top of the code", and stage 2 is piloted.
