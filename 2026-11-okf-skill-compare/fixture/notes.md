# Engineer testimony (synthetic scenario, invented by the experiment author; not a real engineer)

The engineer is not available for more questions. This is everything they said. "Unknown" means they could not answer.

Q1. What is this code and what is a batch?
A1. I maintain this caller for a partner invoice-import integration. A batch is a group of invoice records for one partner account.

Q2. What does "accepted" mean?
A2. Accepted means the vendor queued the batch for asynchronous processing. It does not mean the invoices are posted. The documented response is HTTP 200 or 202 with a JSON object holding a nonempty string submission_id. A separate completion event marks the work complete.

Q3. What does the completion event look like and how fast does it arrive?
A3. Unknown. I don't have its schema, how it correlates to submission_id, or any delivery time promise.

Q4. A timeout returns "unknown". Does the vendor deduplicate batches, so we can resend safely?
A4. Each payload carries our own batch reference but I can't confirm whether the vendor deduplicates on it or for how long. We treat a timeout as unknown, not failed. The passage of time alone never permits a resend. I have no approved replay procedure or vendor contact.

Q5. Why are redirects not followed?
A5. Redirects are not a supported way to move our endpoint for invoice writes. Never follow a Location header to resend invoices or send the bearer token. Endpoint changes need the partner integration owner's confirmation and a reviewed base_url change. I can't tell you who the owner is or the exact steps.

Q6. Why trust_env=False?
A6. This caller runs on dedicated production workers with direct network access to the partner's public-CA HTTPS endpoint. We ignore host environment and netrc so a worker image or a developer login cannot silently change the proxy route, CA source or identity. TLS verification must stay on. A proxy or private-CA deployment is out of scope and needs a designed change.

Q7. Why timeout=(3, 20)?
A7. Unknown. They were here when I inherited the code. I can't give a business deadline or who may change them.
