"""Synthetic invoice-import worker for an interview-skill test; not production code."""

import time

MAX_REQUEUES = 3
REQUEUE_DELAY_S = 300


class Worker:
    def __init__(self, client, store, alerts):
        self.client = client
        self.store = store      # .next_batch(), .mark(batch_id, status, **fields), .requeue(batch_id, delay_s)
        self.alerts = alerts    # .page(message)

    def run_once(self):
        batch = self.store.next_batch()
        if batch is None:
            return False
        try:
            result = self.client.submit(batch["payload"])
        except Exception as exc:  # HTTPError, JSON decode errors and connection errors all land here
            attempts = batch.get("attempts", 0) + 1
            if attempts > MAX_REQUEUES:
                self.store.mark(batch["id"], "failed", error=repr(exc))
                self.alerts.page(f"batch {batch['id']} failed after {MAX_REQUEUES} requeues")
            else:
                self.store.requeue(batch["id"], REQUEUE_DELAY_S)
                self.store.mark(batch["id"], "requeued", attempts=attempts)
            return True
        state = result["state"]
        if state == "accepted":
            self.store.mark(batch["id"], "queued_at_vendor", submission_id=result["receipt"].get("submission_id"))
        elif state == "unknown":
            self.store.mark(batch["id"], "needs_review")
        elif state == "endpoint_changed":
            self.store.mark(batch["id"], "halted")
            self.alerts.page("vendor endpoint moved; stopping the worker")
            raise SystemExit(2)
        return True
