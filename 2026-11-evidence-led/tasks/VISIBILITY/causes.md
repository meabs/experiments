# VISIBILITY: Shopizer's own defects behind the ticket (at 6a4a0a6)

Found by probing the unchanged code through the API before the ticket was written; nothing is planted.

1. **Products have nowhere to keep "visible".** The product entity has only `available`; the API's `visible` field is
   accepted and read back, but is not stored (every product reads `"visible": true`).
2. **`visible` is stored as `available`.** `PersistableProductMapper.merge` sets `available` from the request's
   `visible`, so hiding a product makes it unavailable, and a product sent with `"available": false` is available.
3. **Shopper reads, lists and carts don't filter on visibility** (probe: a product sent hidden opens by sku and is in
   the v1 and v2 public lists); nothing stops checkout of a cart holding one.
4. **There is no merchant-side product list**: the only list is the public one, and the token filter does not
   authenticate public paths, so a merchant view needs its own protected endpoint.
5. **Errors come out wrong** (as in STOCK): checkout wraps every exception in a 400, so refusing a hidden product
   can't be the 409 the ticket asks for without unwrapping.

Three hidden tests (a visible product opens by friendly URL, showing a product again brings it back, orders are
unaffected) pass on the unchanged code: they guard behaviour the change must keep.
