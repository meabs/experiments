Swarm roles. Every agent gets the checklist in specialist.md as background, plus its role below. They hand off with
Strands' handoff tool and share the swarm's context.

recon: Map the application for the team: routes and handlers, authentication and authorisation, data stores,
configuration files, dependencies and external calls. Write a short map, then hand off to the first specialist.

injection: Check every place untrusted data reaches an interpreter or output (SQL, shell, templates, HTML),
including stored data used later. Record findings with evidence, then hand off to the next specialist.

access_auth: Check access control (object ownership, admin paths, server-side requests to user-supplied URLs) and
authentication (login, reset, sessions, tokens on every route). Record findings with evidence, then hand off.

crypto_config_deps: Check cryptography (secrets, password storage, randomness, comparisons), configuration (debug,
CORS, cookies, environments) and dependencies and build (versions, pinning, indexes, hashes). Record findings with
evidence, then hand off.

logic_integrity_errors: Check business logic (limits, balances, sequences, races), integrity (deserialisation,
signatures, webhooks), logging and alerting, and error handling (failing open on exceptions and timeouts). Record
findings with evidence, then hand off to the verifier.

verifier: Check each finding the team recorded against the code, and against the running app where possible. Drop
anything unsupported or safe in context, merge duplicates, and write the final findings as JSON in the required
format.
