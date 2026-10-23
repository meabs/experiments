# Stage 6 — Comprehension Test (Rerun 3)

Target: `design_draft.md`
Reviewer: `egm-comprehension` (Comprehension Goldfish)

One residual wording conflict was found: the detailed API entry still said a
deleted ID returns 404 on a later GET even though the design explicitly defines
no item-GET endpoint. That wording has been removed; collection GET simply no
longer lists the deleted code, while PUT/DELETE return 404.
