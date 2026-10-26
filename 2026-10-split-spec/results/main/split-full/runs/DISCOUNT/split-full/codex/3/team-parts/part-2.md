Part 2 — admin discounts API and DTOs

Read TASK.md first. Own the shop-facing admin REST contract for /api/v1/private/discounts plus request/response DTOs in sm-shop and sm-shop-model. Implement protected POST/GET/PUT/DELETE endpoints, store resolution via ?store= and status/error mapping (201 create, 409 duplicate, 400 validation, not-found handling) matching existing private API conventions. Depend on Part 1's DiscountService and Discount domain methods; do not modify cart facade/mapper or core model/service files except where unavoidable for compilation.
