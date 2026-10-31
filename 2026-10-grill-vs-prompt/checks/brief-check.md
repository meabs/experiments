# Brief check: fresh reader's report (2026-10-31, before any measured run)

The reader was `openai/gpt-6-luna` through OpenRouter, with no part in writing the tasks. For each new ticket it was
given the ticket, the brief, the hidden tests and the repository files the ticket touches, and asked whether
each left-out requirement is reasonable, correctly labelled and fairly tested. Its answers are below as it
gave them. What was changed in response is in the README's amendment log.

## M1

- **ra — `accounts:write` scope**
  - **Reasonable:** Yes. This is a write operation, and the API’s security conventions apply.
  - **Label:** Right. The README explicitly says data-changing endpoints need `accounts:write`.
  - **Fairly tested:** Yes. The test checks for 403 and verifies that the limit did not change.
  - **Verdict: OK**

- **rb — closed accounts cannot be changed**
  - **Reasonable:** Yes. A closed account is a plausible state in which a change should be refused.
  - **Label:** Right. The account status and the README’s 409 state-conflict convention are in the repo; closure code also shows that closed status is meaningful.
  - **Fairly tested:** Yes. The test expects 409 and verifies no change.
  - **Verdict: OK**

- **rc — assigned support can lower but not raise; admins can raise**
  - **Reasonable:** Yes, this is a meaningful authorization distinction that should be clarified.
  - **Label:** Wrong as stated. `Account.java` says the limit is set by bank admins, not customers, which points against allowing support to change it. The ticket’s broad reference to “staff” does not resolve that conflict.
  - **Fairly tested:** The tests cover a support reduction, support refusal to raise, and an admin increase. They do not test the stated rule that setting the same value counts as lowering.
  - **Verdict: CHANGE: Resolve the conflict with the repo’s admin-only description, and test the same-value case if that rule remains.**

- **rd — £5,000 ceiling**
  - **Reasonable:** No, not as an unstated requirement: it directly conflicts with the ticket’s promise to accept any whole number of 0 or more.
  - **Label:** The ceiling itself is absent from the repo, but the ticket points against it.
  - **Fairly tested:** No. A correct implementation following the ticket and accepting 5001 would fail.
  - **Verdict: CHANGE: Put the ceiling in the ticket and reconcile it with the stated input range, or remove the requirement and test.**

- **re — savings accounts cannot be changed**
  - **Reasonable:** This could be a product rule, but it is not a reasonable hidden constraint against a ticket that says to change an account’s limit without excluding savings accounts.
  - **Label:** The fixed-savings rule is absent from the repo, but the ticket’s general scope points against the restriction.
  - **Fairly tested:** The test checks that the operation is refused and that the value remains unchanged, but it accepts almost any 4xx rather than requiring the brief’s stated 409.
  - **Verdict: CHANGE: Specify the savings-account exception in the ticket and make the test require 409.**

- **rf — every change adds an internal audit note**
  - **Reasonable:** Yes. Recording a financial-limit change for staff review is a plausible requirement to clarify.
  - **Label:** Right. The repo has internal notes, but does not say that daily-limit changes must create one.
  - **Fairly tested:** The test checks an internal note, its author, and both limit values without requiring exact wording. It only exercises one change, so it does not establish the “every change” part.
  - **Verdict: OK**

**Other fairness issue:** The hidden tests do not check decimal input, despite the ticket requiring a whole number. This is an under-testing gap, not a false failure. The 5001 test is the clear false-failure risk because it contradicts the ticket.

## N1

- **ra — `accounts:write` scope (in the repo):** Reasonable and correctly labelled: the README explicitly requires this scope for data-changing endpoints. The hidden test checks rejection and that the balance is unchanged. **OK**
- **rb — credits over £100 require approval (in my head):** It is reasonable to clarify whether large credits need sign-off, and the parent question could plausibly be asked up front. But the ticket says a credit adds the amount to the balance and books a transaction, which points against this exception. The rule is absent from the repo, but it conflicts with the ticket rather than being an unstated detail the agent should discover. The test checks immediate versus delayed payment at £100, but does not check that the delayed credit is actually saved with status `PENDING`. **CHANGE: Put the approval threshold and pending status in the ticket, or remove the hidden rule; test the pending status.**
- **rc — approval process (in my head; child of rb):** The specific endpoint, role, tenant restriction, and response are not stated in the ticket. The repository’s closure-approval flow is a useful precedent, but does not establish these goodwill-credit rules. The nesting is plausible and the stated question flow makes the child reachable only after the agent learns about approval. Testing is incomplete: the tests do not check the returned credit, `PAID` status, or the required 409 for approving a non-pending credit. They also allow either 403 or 404 where the brief specifies which one applies. **CHANGE: Test the specified response and status, repeated-approval 409, and exact 403/404 distinctions.**
- **rd — an initiator cannot approve their own credit (in my head; child of rb):** This is a reasonable separation-of-duties rule, absent as a goodwill-credit rule in the repo. It is reachable only after the approval step is introduced, as required. The test checks the self-approval 403 and that the credit can still be approved by someone else. **OK**

**Other fairness issue:** The rb rule makes a correct literal implementation of the ticket fail for credits over £100. The hidden tests should not enforce that exception unless the ticket states it.

## N2

- **ra — write scope (in the repo):** Reasonable and findable: the README says data-changing endpoints require `accounts:write`. The test checks a read-only token is forbidden and the request stays pending, though it does not check that *all* state (for example, the account) is unchanged.
- **rb — pending only (in the repo):** Reasonable. The status enum, pending-request listing, existing pending-state check, and README’s 409 convention point toward this rule. The test covers an already-approved request, but not a rejected one; add a rejected-request case to verify the stated “not PENDING” rule rather than only one example.
- **rc — money must move (in my head, parent):** Reasonable to ask about before approving a closure. Balances and transactions exist in the repo, but nothing there or in the ticket says a non-zero balance must be transferred, names the body field, or specifies the 409 behavior. The tests cover both missing-transfer conflicts and a successful transfer. The parent is plausibly askable up front.
- **rd — eligible destination (in my head, child):** Reasonable once the need to transfer is known. The repo describes tenants as banks and exposes customer and account status, but does not specify these transfer restrictions. The tests exercise different customer, different bank, closed, same-account, and nonexistent destinations, and accept any 4xx as the brief requires. It is reachable only after the transfer question.
- **re — recording the transfer (in my head, child):** Reasonable once a transfer is established, and absent from the ticket and repo. The tests verify the debit and credit amounts and resulting balances. They do not pin down a description, which is appropriate given the brief leaves wording to the implementer. It is reachable only after the transfer question.

**Other test gaps:** The successful ticket test does not verify the returned response has the same full shape as `GET /api/closure-requests` (for example, `requestedBy` and `requestedAt`). Several “nothing changes” checks inspect the request and some account state, but not every possible side effect, such as transactions. These are coverage gaps, not reasons a correct implementation should fail.

- **ra — OK**
- **rb — CHANGE: test a `REJECTED` request as well as an `APPROVED` one.**
- **rc — OK**
- **rd — OK**
- **re — OK**
