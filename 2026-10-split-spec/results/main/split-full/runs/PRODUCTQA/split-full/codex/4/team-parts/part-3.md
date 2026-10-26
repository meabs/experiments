# Part 3 — admin API

Read `TASK.md` first. Own the admin controller layer under `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1` (create a focused questions/admin controller; do not edit the customer/public controller from Part 2). Implement, protected like existing `/private` endpoints and scoped to `?store=`:

- `GET /api/v1/private/questions?status=PENDING` (default PENDING), accepting only PENDING/PUBLISHED/REJECTED, returning full question JSON oldest asked first and 400 for any other status;
- `PUT /api/v1/private/questions/{id}/answer` with `{answer}` returning 200, publishing and replacing an existing answer;
- `PUT /api/v1/private/questions/{id}/reject` returning 200 and setting REJECTED.

Use Part 1's `ProductQuestionService` and DTOs. Map unknown ids to 404, invalid answer length/content to 400, and answering REJECTED to 409. Ensure store scoping and existing admin authorization conventions. Do not implement persistence or customer/public routes.
