# STOCK: Shopizer's own defects behind the ticket (at 6a4a0a6)

Found by probing the unchanged code through the API before the ticket was written; nothing is planted.

1. **Checkout takes stock from the wrong product.** `OrderServiceImpl.process` looks the product up with
   `productService.getById(orderProduct.getId())`: the order line's id, not the product's. The ordered products keep
   their stock, and whichever product shares the line's id loses it (probe: 20/20 before and after an order of 2 and 3).
2. **No stock check at checkout.** The same loop only logs when stock is short, then lets the quantity go negative
   or below zero (probe: 5 ordered with 2 in stock, order placed).
3. **No stock check in the cart.** `ShoppingCartFacadeImpl` refuses a product only when its stock is exactly 0
   (probe: 10 accepted with 3 in stock); creating, changing and multi-changing a cart all go through it.
4. **Cancelling never restocks.** `OrderFacadeImpl.updateOrderStatus` only records the new status; a canceled order
   can also be reopened.
5. **Out-of-stock products show as available.** `ReadableProductMapper` copies the merchant's flag only.
6. **The merchant's "available" flag is lost on creation.** `PersistableProductMapper.merge` sets `available` from
   the request's `visible` field.
7. **Errors come out as 400.** The cart and checkout endpoints wrap every exception in `ServiceRuntimeException`
   (HTTP 400), so a refusal can't come back as the 409 the ticket asks for without unwrapping.
