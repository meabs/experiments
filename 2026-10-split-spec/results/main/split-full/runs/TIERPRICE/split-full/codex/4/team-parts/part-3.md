Part 3: quantity-tier pricing in cart responses and recalculation.

Own these files (and any new files in the same cart/calculation packages needed for this part):
- sm-core/src/main/java/com/salesmanager/core/business/services/shoppingcart/ShoppingCartCalculationServiceImpl.java and related order/cart pricing implementation files it must change
- sm-shop/src/main/java/com/salesmanager/shop/populator/shoppingCart/ShoppingCartDataPopulator.java
- sm-core-model/src/main/java/com/salesmanager/core/model/shoppingcart/ShoppingCartItem.java and/or sm-shop-model cart response classes only as needed for pricing output

Make every cart calculation/retrieval dynamically choose the largest reached tier for each line's own Product, unless the product's effective own price (including special price) is lower. Recompute after quantity or tier changes, including carts already persisted. Ensure each returned line has subTotal = effective unit price * quantity and cart subtotal/total reflect those values. Do not apply one product's tiers to another line; preserve existing promotions/taxes behavior as far as possible.

Relies on Part 1 exposing product tiers (or a tier pricing helper/service) and existing Product price/special-price APIs. Part 2 only changes tiers through Part 1 and needs no direct edits from this part.
