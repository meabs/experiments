A merchant deleted an old "Summer sale" category, and every product that was only in that category disappeared from the shop: the products are gone, carts that held them stopped working, and orders that included them can no longer be opened. Opening the deleted category by its id now shows a server error rather than "not found".

Deleting a category (DELETE /api/v1/private/category/{id}) must delete only the category and the categories below it:

- Its products are kept, with their stock, price and any other categories. They are just no longer in the deleted categories: GET /api/v2/product/{sku} doesn't list those categories any more.
- Carts and orders that hold its products are unaffected: they read, change and check out exactly as before.
- Categories below the deleted one are deleted with it, and their products are kept in the same way.
- A deleted category gives HTTP 404 Not Found from GET /api/v1/category/{id}, isn't in GET /api/v1/category, and listing its products (GET /api/v1/products?category={id}) lists none.
- Deleting a category that doesn't exist gives HTTP 404 Not Found.

When you have finished, reply with one short paragraph saying what you changed.
