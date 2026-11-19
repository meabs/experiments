# <A question the experiment answers?> (experiment <ID>)

**Status:** draft design, <date>. No measured run yet. Later changes go in the amendment log (section 10).

## 1. Question

What do you want to find out, in plain words? One to three numbered questions at most.

## 2. Why it is worth testing

What is claimed or adopted without measurement? What have earlier experiments here found (link them), and what would
change if this one comes out each way?

## 3. What is being changed: the arms

One variable per arm. A table: arm id, what the agent gets, how it is built (files in `arms/<ARM>/`, a prompt suffix, an
installed tool with its pinned version). Say what is held constant: agent, model, effort, repository commit, tickets.

## 4. The tickets or fixtures

What the agent is asked to do, where the hidden tests or the verifier live, how the safe and the failing routes are
distinguished. Say how you checked the fixtures (self-test) and the **pilot rule** that retires a ticket.

## 5. Measures

The primary measure (and why), then secondary ones: cost at list price, tokens, time, process evidence counted from files
in the change, false success claims. Say where each number is read from.

## 6. Hypotheses and analysis

Directional hypotheses, each testable, written before the run. Test: one-sided permutation within ticket, bootstrap
intervals, Holm correction within each group. Anything else is exploratory.

## 7. Size, cost and time

Runs = tickets x arms x repetitions, pilot size, estimated cost with a ceiling, expected wall-clock time.

## 8. Rounds (optional)

What a second round would add (held-out tickets, other agents).

## 9. Limits known in advance

One agent, one model, one repository, repetitions, what the arms do not test.

## 10. Amendment log

Date, what changed, why, and whether it was before or after any measured run.
