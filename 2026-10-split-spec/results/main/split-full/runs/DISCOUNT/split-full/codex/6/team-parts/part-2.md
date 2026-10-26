## Part 2 — private discount management API

Read `TASK.md` first, then implement only this part. Own the admin-facing HTTP layer; do not edit the discount domain/service files from part 1 or cart files from part 3.

### Files owned

- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/discount/**` (new controller)
- `sm-shop/src/main/java/com/salesmanager/shop/store/controller/discount/**` (facade/mapper only if needed)
- Any API-layer discount tests under `sm-shop/src/test/**` that you add.

### What to implement

Add protected-style endpoints matching existing `/api/v1/private` conventions, with the store resolved from `?store=`/`MerchantStore`:

- `POST /api/v1/private/discounts` → 201 and stored object including id
- `GET /api/v1/private/discounts`
- `PUT /api/v1/private/discounts/{id}`
- `DELETE /api/v1/private/discounts/{id}`

Accept/return the JSON fields in `TASK.md`, including defaults and category arrays. Map validation failures to HTTP 400, duplicate code conflicts to 409, and missing/wrong-store ids appropriately (normally 404). Follow existing authentication/store injection and exception conventions in neighboring APIs. Call part 1’s service methods rather than duplicating persistence or validation. Run focused Maven tests/compile.

### Dependencies supplied by other parts

Part 1 supplies the discount service/domain (CRUD, validation, duplicate detection, store scoping). Part 3 is independent at runtime but will consume the same service; preserve JSON property names and id behavior expected by it.
