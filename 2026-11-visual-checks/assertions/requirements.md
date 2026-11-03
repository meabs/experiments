# What each screen must show (written 2026-11-03, before any defect was designed)

These come from what a shopper needs on each screen of this storefront, not from the planted defects (none existed
when this was written). Every assertion in `assertions.json` is a yes/no question where **yes means the screen is
fine**. The same assertions apply at desktop and mobile size.

## Every screen
- The shop's header (language, phone number, navigation, account and cart icons) is shown and readable.
- No text overlaps other text, and no element covers another one it shouldn't.
- Nothing runs off the side of the screen.
- No raw template text or code is shown in place of real values.

## Home
- The hero banner shows a heading and a "Shop now" button.

## Category (product list)
- Products are shown as cards, each with a picture, a name and a price.
- Every product picture has loaded.

## Product page
- The product's picture, name and price are shown.
- The price is in US dollars, like the rest of the shop.
- There is a quantity selector and an Add to cart button.

## Cart
- Each cart line shows the product, its unit price, quantity and line subtotal.
- Each line's subtotal equals unit price times quantity.
- The cart total is shown and equals the sum of the lines.
- There is a way to proceed to checkout.

## Checkout
- The billing form is shown with labelled fields.
- The order summary lists the products and a total.
- There is a Place your order button, visible and not covered.
