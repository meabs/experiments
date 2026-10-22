Our marketing team prepares storefront content boxes (banners, footer notes) ahead of time and keeps them hidden (visible = false) until they go live. Shoppers are seeing them early: the storefront's box list (GET /api/v1/content/boxes) includes hidden boxes, and a hidden box can be read at GET /api/v1/content/boxes/{code}.

Hidden boxes must not reach shoppers: the storefront list must leave them out, and reading a hidden box by code from the storefront must answer 404 Not Found.
