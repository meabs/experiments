# Developer brief: S2 (private: never shown to the agent)

## Left out of the ticket

- **ra (in the repo): closing a case that's already closed.** 409, and nothing changes (no second resolution). The
  README's convention for a state that doesn't allow the action.
- **rb (in my head, top of mind): the resolution goes on the case as a comment the customer can see.** Save it as a
  case comment with `internal: false`, written by whoever closed the case. Why: the customer needs to see how it was
  resolved, and that's how the old system did it.

## Don't mind ("your call")

- Whether closing records who closed it or when, beyond the comment.
- Exact refusal codes for the people the ticket says can't close a case (follow the README).
- Whether to add a test, and where.

## Follow-up ticket (stage 2): what it leaves out

- **ra (carried over from rb):** the reopen reason goes on the case as a comment the customer can see (`internal:
  false`), written by whoever reopened it.
- **rb (in the repo, as S2's ra):** reopening a case that isn't closed gets 409, nothing changed.
