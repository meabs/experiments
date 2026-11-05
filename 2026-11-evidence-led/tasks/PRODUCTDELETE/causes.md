# PRODUCTDELETE: Shopizer's own defects behind the ticket (at 6a4a0a6)

Found by probing the unchanged code through the API before the ticket was written; nothing is planted.

1. **`ProductService.getBySku` throws when there is no such product**, while its callers check for null: the cart
   (each line's product is looked up by sku), the order line view (`ReadableOrderProductPopulator`) and adding to a
   cart. Once a product is deleted, every cart and order that mentions it fails (probe: cart 400, order 500).
2. **A cart with a missing product is deleted on read.** `ShoppingCartServiceImpl.getPopulatedShoppingCart` marks the
   cart obsolete, and the facade then deletes the cart, which fails on its remaining lines' foreign key.
3. **Checkout looks products up by the order line's id** (`productService.getById(orderProduct.getId())`, as in
   STOCK). When that id belongs to a deleted product, checkout of an unrelated cart fails.
