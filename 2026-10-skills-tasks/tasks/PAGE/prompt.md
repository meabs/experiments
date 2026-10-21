A developer building our storefront reports: "Paging through the product list doesn't work. GET /api/v2/products?count=20&page=1 returns exactly the same products as page=0, and so does every other page."

Make paging work for the v2 product list, so each page returns the next set of products and a page past the end returns none.
