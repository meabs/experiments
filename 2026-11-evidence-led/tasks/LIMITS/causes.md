# LIMITS: Shopizer's own defects behind the ticket (at 6a4a0a6)

Found by probing the unchanged code through the API before the ticket was written; nothing is planted.

1. **Limits are never stored.** `PersistableProductAvailabilityMapper` sets every product's stock record to minimum 1
   and maximum 1, whatever the request's `quantityOrderMinimum` and `quantityOrderMaximum` say (probe: created with 2
   and 4, read back as 1 and 1).
2. **Replacing a product adds a second stock record.** `PersistableProductMapper.merge` always adds a new default
   availability instead of updating the existing one, and the product view reads whichever the set returns first,
   so an update's values may never show.
3. **No maximum is shown as 1.** `ReadableProductMapper` shows a missing maximum as 1 rather than "no limit".
4. **Carts and checkout ignore the limits** (probe: 1 accepted with minimum 2, 9 accepted with maximum 4). Because
   every stored maximum is 1 (cause 1), enforcing limits without fixing storage would cap every product at one.
5. **Errors come out wrong.** Product creation can't return 400 for invalid limits without a validation path, and
   checkout wraps every exception (400), so a limits refusal can't be the 409 the ticket asks for without unwrapping.

Three hidden tests (a quantity of 0 removes, a cart within the limits checks out, products without limits work as
before) pass on the unchanged code: they guard behaviour the change must keep.
