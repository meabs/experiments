---
okf_version: "0.2"
---

# Repository knowledge: accounts-service

Curated by the Accounts squad. It records what the code doesn't say well: the service's key facts and pitfalls, the
external systems it talks to and how they behave, and the business processes it supports. It does not describe the
code file by file: read the code for that.

## Start here

- [System information](/system.md) - what the service is, how to build, run and test it, and its key pitfalls. Read
  before any change.
- [Architecture](/architecture.md) - components, the payment flow, and each external system's rules and failure
  behaviour (scheme gateway, fraud screening, core ledger, notifications). Read before touching `payment` or
  `integration`.
- [System context](/context.md) - the service's role in the bank, the business processes end to end, who depends on
  it and what they need. Read for anything about risk, operations or the effect of a change on other teams.
