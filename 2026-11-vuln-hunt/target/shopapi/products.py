"""Catalogue, search, reviews and product pages."""
import hashlib

import bleach
from flask import Blueprint, abort, g, jsonify, make_response, render_template, request

from . import cache
from .auth import require_auth
from .db import get_db

bp = Blueprint("products", __name__)
SORT_COLUMNS = {"name", "price_pence", "stock"}
ALLOWED_TAGS = ["p", "em", "strong", "ul", "ol", "li", "br", "a"]


def product_json(p):
    return {"id": p["id"], "sku": p["sku"], "name": p["name"], "price_pence": p["price_pence"], "stock": p["stock"],
            "image": p["image"]}


@bp.get("/products")
def list_products():
    sort = request.args.get("sort", "name")
    if sort not in SORT_COLUMNS:
        sort = "name"
    order = "DESC" if request.args.get("desc") == "1" else "ASC"
    key = f"products-{sort}-{order}"
    rows = cache.get(key, max_age=300)
    if rows is None:
        rows = [product_json(p) for p in get_db().execute(f"SELECT * FROM products ORDER BY {sort} {order}")]
        cache.put(key, rows)
    return jsonify(rows)


@bp.get("/products/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    rows = get_db().execute(
        "SELECT * FROM products WHERE name LIKE '%" + q + "%' OR sku LIKE '%" + q + "%' ORDER BY name LIMIT 50"
    ).fetchall()
    return jsonify([product_json(p) for p in rows])


def description_html(md):
    """Very small Markdown subset (paragraphs, *em*, **strong**, - lists), then cleaned."""
    out = []
    for block in md.split("\n\n"):
        lines = block.strip().splitlines()
        if lines and all(l.startswith("- ") for l in lines):
            out.append("<ul>" + "".join(f"<li>{l[2:]}</li>" for l in lines) + "</ul>")
        elif lines:
            out.append("<p>" + "<br>".join(lines) + "</p>")
    html = "".join(out)
    html = html.replace("**", "\0")
    parts = html.split("\0")
    html = "".join(p if i % 2 == 0 else f"<strong>{p}</strong>" for i, p in enumerate(parts))
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes={"a": ["href"]}, strip=True)


@bp.get("/p/<sku>")
def product_page(sku):
    db = get_db()
    p = db.execute("SELECT * FROM products WHERE sku = ?", (sku,)).fetchone()
    if p is None:
        abort(404, "no such product")
    reviews = db.execute("SELECT * FROM reviews WHERE product_id = ? ORDER BY id DESC LIMIT 20", (p["id"],)).fetchall()
    body = render_template("product.html", product=p, description=description_html(p["description_md"]),
                           reviews=reviews)
    etag = hashlib.md5(body.encode()).hexdigest()
    if request.if_none_match.contains(etag):
        return "", 304
    resp = make_response(body)
    resp.set_etag(etag)
    return resp


@bp.post("/products/<int:product_id>/reviews")
@require_auth
def add_review(product_id):
    data = request.get_json(force=True)
    body = (data.get("body") or "").strip()
    rating = int(data.get("rating", 0))
    if not body or len(body) > 2000 or not 1 <= rating <= 5:
        abort(400, "a review needs text (up to 2,000 characters) and a rating from 1 to 5")
    db = get_db()
    if db.execute("SELECT 1 FROM products WHERE id = ?", (product_id,)).fetchone() is None:
        abort(404, "no such product")
    db.execute("INSERT INTO reviews (product_id, author_id, author_name, rating, body) VALUES (?, ?, ?, ?, ?)",
               (product_id, g.user["id"], g.user["display_name"], rating, body))
    db.commit()
    return jsonify(ok=True), 201
