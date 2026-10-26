Part 3 owns shopper promo application and cart presentation/calculation integration.

Replace the hard-coded promo behavior in POST /api/v1/cart/{cartCode}/promo/{code} with DiscountService lookup/evaluation. Preserve the previous cart code on rejected applications (400), replace valid codes, and remove one-day expiry. Recalculate on every cart read/update so inactive/expired/edited/deleted/non-eligible codes are dropped. Populate promoCode as stored merchant spelling, add positive discount total line, and set total=subtotal-discount with half-up 2-decimal rounding; honor category descendants and eligible-item subtotal via the service contract from part 1.

Own shopping-cart API/facade/mapper/populator/calculation files under sm-shop plus any cart model files needed for promoCode/totals. Do not edit discount CRUD API files (part 2) or core discount entity/service implementation (part 1) except where a tiny integration hook is unavoidable.
