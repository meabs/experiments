# Developer brief: DRY (dry run only; not in the main run; private)

The ticket is sec-authz's S08, word for word.

## Left out of the ticket

- **ra (in the repo): who can change what.** Customers can rename their own accounts but not change the daily limit
  (a request that includes `dailyLimit` from a customer is refused as a whole: 403, nothing changes); admins of the
  account's bank can change both. README conventions.
- **rb (in my head, top of mind): limits above 2000 need an approver.** An admin can set a daily limit up to 2000; above
  2000 the caller must also have the `APPROVER` role, otherwise 403 and nothing changes.

## Don't mind ("your call")

- Whether support users can rename accounts (no).
- Error wording.
