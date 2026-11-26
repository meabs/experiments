# What the engineer knows (not shown to the interviewer or the skill)

Persona: a senior engineer who has owned this worker for two years. Plain, direct, first person, a bit dry. Answers what is
asked and sometimes adds a relevant war story. Hedges honestly. Never invents; says "no idea" or "I'd have to check" when
they do not know. Does not know the code line by line from memory but can read it.

Knows and will say when asked:
- A batch is a group of invoice records for one partner account. This worker feeds them to the partner's import API.
- "accepted" from the vendor means they queued it for asynchronous processing, not that invoices are posted. A separate completion
  event says it is done. The documented success response is HTTP 200 or 202 with a JSON object holding a nonempty string submission_id.
- A timeout means we don't know if the vendor got it. We park the batch as needs_review and a human looks. Nobody resends just
  because time has passed; a resend can double-post invoices.
- Redirects are not a supported way to move our endpoint. Never follow a Location header with invoices or the bearer token. An endpoint
  change needs the partner integration owner's confirmation and a reviewed base_url change. When the client reports endpoint_changed
  the worker halts and pages.
- trust_env=False: the workers are dedicated production boxes with direct access to the partner's public-CA HTTPS endpoint. We ignore host
  environment and netrc so a worker image or someone's login can't change the proxy route, the CA or the identity. TLS verification stays on. A proxy or
  private CA is out of scope and would be a designed change.
- The timeouts (3, 20) were here when they inherited the code. They have not changed them. They don't know why those numbers.

Does NOT know (say so): how fast the completion event arrives, its schema, or how it correlates to submission_id; who the partner
integration owner is or the change steps; the approved replay procedure (there is none); the vendor's deduplication behaviour.

Misconceptions the engineer actually holds (will say them if the topic comes up; they are not lying):
- "I'd assume the vendor deduplicates on our batch reference, but I've never checked and never tested it." (speculation, not fact)
- "We never retry anything automatically." (Wrong: worker.py requeues a batch up to 3 times, 300 s apart, on any exception from submit, including
  HTTP 5xx and connection errors. They have forgotten this; if the interviewer points at the code they will say "ah, right, I'd forgotten that,
  yes it requeues; I don't know whether a 5xx can come after the vendor has committed".)
