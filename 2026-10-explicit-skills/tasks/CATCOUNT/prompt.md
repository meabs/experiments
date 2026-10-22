Every category returned by the category list REST API (GET /api/v1/category) has a "productCount" field, but it is always 0.

Make productCount show the number of products in the category or in any of its subcategories (at any depth), counting each product once even when it sits in several of those categories. Every category in the list must be right, including the categories nested inside "children".
