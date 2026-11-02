"""Product images: staff import them from our CDN or a supplier's photo library by URL."""
import ipaddress
import os
import secrets
import socket
import subprocess
from urllib.parse import urlparse

import requests
from flask import Blueprint, abort, current_app, g, jsonify, request, send_from_directory

from .auth import require_auth
from .db import get_db

bp = Blueprint("images", __name__)
MAX_BYTES = 5 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def host_is_public(host):
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    return all(ipaddress.ip_address(i[4][0]).is_global for i in infos)


def check_url(url):
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        abort(400, "image URL must be http or https")
    if u.hostname not in current_app.config["IMAGE_HOSTS"]:
        abort(400, "images can only be imported from approved hosts")
    if not host_is_public(u.hostname):
        abort(400, "image host doesn't resolve to a public address")


def sniff_type(path):
    out = subprocess.run(["file", "--brief", "--mime-type", path], capture_output=True, text=True, timeout=10)
    return out.stdout.strip()


@bp.post("/products/<int:product_id>/image")
@require_auth
def import_image(product_id):
    if g.user["role"] != "staff":
        abort(403, "staff only")
    url = (request.get_json(force=True).get("url") or "").strip()
    check_url(url)
    r = requests.get(url, timeout=10, stream=True)
    if r.status_code != 200:
        abort(400, f"couldn't fetch the image ({r.status_code})")
    data = r.raw.read(MAX_BYTES + 1, decode_content=True)
    if len(data) > MAX_BYTES:
        abort(400, "image is larger than 5 MB")
    name = secrets.token_hex(8)
    path = os.path.join(current_app.config["IMAGE_DIR"], name)
    with open(path, "wb") as f:
        f.write(data)
    kind = sniff_type(path)
    if kind not in IMAGE_TYPES:
        os.remove(path)
        abort(400, f"not an image we accept ({kind}); first bytes: {data[:64]!r}")
    final = name + IMAGE_TYPES[kind]
    os.replace(path, os.path.join(current_app.config["IMAGE_DIR"], final))
    db = get_db()
    db.execute("UPDATE products SET image = ? WHERE id = ?", (final, product_id))
    db.commit()
    return jsonify(image=final)


@bp.get("/images/<name>")
def image_file(name):
    return send_from_directory(current_app.config["IMAGE_DIR"], name)
