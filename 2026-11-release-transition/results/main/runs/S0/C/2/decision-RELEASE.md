# Decision release

## Rollout order

Deploy decision instances one at a time using the normal rolling order. No
`deploy_after`, `atomic_with`, or queue drain constraint is required: the
service has no persistent schema or queued-event change, and its only contract
change is additive.

## Mixed old and new versions

Both versions continue to accept `score {income, amount}`. Old decision
instances return `{score}`; new instances return `{score, reason}`, where
`reason` is `ratio <n>%` and `n` is `amount * 100 / income` using integer
arithmetic. Existing customer instances ignore the additional response field,
so traffic can be sent to either version while rollout is in progress. The new
customer version can use `reason` when it receives a response from a new
decision instance and remains compatible with an old response that has no
`reason` during the transition.

## Rollback

If the rollout fails, stop deploying new instances and route traffic back to
the old decision version or redeploy the replaced instances with the old
version. No database migration, event replay, or queue cleanup is needed; the
old version remains able to serve the original request and response contract.
