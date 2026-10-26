## Part 1 — discount domain and service

Read `TASK.md` first. Own the discount persistence/domain and the service contract used by the API and cart; do not edit files assigned to parts 2 or 3 unless compilation absolutely requires a tiny compatibility adjustment.

### Files owned

- `sm-core-model/src/main/java/com/salesmanager/core/model/discount/**` (new discount entity/type as needed)
- `sm-core/src/main/java/com/salesmanager/core/business/repositories/discount/**`
- `sm-core/src/main/java/com/salesmanager/core/business/services/discount/**`
- `sm-shop-model/src/main/java/com/salesmanager/shop/model/discount/**` (request/read DTOs if useful to keep API mapping clean)

### What to implement

Create a store-scoped discount code model with id, merchant store, code, type (`PERCENT`/`AMOUNT`), value, optional minimum subtotal, start/end dates, category codes, and active flag. Persist category codes in a practical JPA-compatible form. Add repository queries for store listing, case-insensitive lookup, duplicate detection, and id/store lookup. Add a Spring service that validates required fields, type/value/date/category rules, validates category codes through the existing category service, enforces case-insensitive uniqueness per store (including rename), applies defaults (active=true and start=today), and exposes operations needed by the API and cart.

Expose clear methods, at minimum equivalents of:

- `List<Discount> list(MerchantStore store)`
- `Discount create/update/delete/get` scoped to a store
- `Discount findByCode(MerchantStore store, String code)` (case-insensitive)
- a calculation/eligibility method taking a cart/store and returning whether applicable plus rounded discount and eligible subtotal, or an equivalent API that part 3 can use.

Use existing `CategoryService`, product/category relationships, and store ownership checks as appropriate. Throw/use recognizable exceptions so part 2 can map bad input to 400 and duplicates to 409. Run focused Maven compilation/tests for the modules you touch.

### Dependencies supplied by other parts

Part 2 will call your service for CRUD and map your domain/DTO to HTTP responses. Part 3 will call your lookup/eligibility/calculation methods from the cart facade/mapper and will rely on your `Discount` fields and semantics. Keep public names stable and communicate any necessary choices in your completion message.
