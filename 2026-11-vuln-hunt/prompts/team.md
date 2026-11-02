Team roles (arm C as a Strands Graph: recon, then the four specialists in parallel, then the verifier). Every agent
gets the checklist in specialist.md as background, plus its role below. Each agent sees the original task and the
final messages of the agents before it.

recon: Map the application for the team: routes and handlers, authentication and authorisation, data stores,
configuration files, dependencies and external calls. End with the map as your final message.

injection: Check every place untrusted data reaches an interpreter or output (SQL, shell, templates, HTML),
including stored data used later. End with your findings as your final message, each with file, line and evidence.

access_auth: Check access control (object ownership, admin paths, server-side requests to user-supplied URLs) and
authentication (login, reset, sessions, tokens on every route). End with your findings as your final message, each
with file, line and evidence.

crypto_config_deps: Check cryptography (secrets, password storage, randomness, comparisons), configuration (debug,
CORS, cookies, environments) and dependencies and build (versions, pinning, indexes, hashes). End with your findings
as your final message, each with file, line and evidence.

logic_integrity_errors: Check business logic (limits, balances, sequences, races), integrity (deserialisation,
signatures, webhooks), logging and alerting, and error handling (failing open on exceptions and timeouts). End with
your findings as your final message, each with file, line and evidence.

verifier: You receive every specialist's findings. Check each one against the code, and against the running app
where possible. Drop anything unsupported or safe in context, merge duplicates, and call submit_findings once with
the complete final list.
