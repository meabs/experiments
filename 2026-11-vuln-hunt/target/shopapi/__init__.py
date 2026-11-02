"""Hartley & Finch shop API."""
import logging
import os

from flask import Flask, abort, g, jsonify, request

from . import db

log = logging.getLogger("shopapi")


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object("config")
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.config["IMAGE_DIR"], exist_ok=True)
    os.makedirs(app.config["CACHE_DIR"], mode=0o700, exist_ok=True)

    db.init_app(app)

    from . import admin, auth, basket, giftcards, images, orders, payments, products
    for bp in (auth.bp, orders.bp, products.bp, basket.bp, giftcards.bp, images.bp, payments.bp, admin.bp):
        app.register_blueprint(bp)

    admin_paths = {r.rule for r in app.url_map.iter_rules() if r.endpoint.startswith("admin.")}

    @app.before_request
    def log_request():
        if request.method in ("POST", "PUT", "PATCH"):
            log.info("%s %s %s", request.method, request.path, request.get_data(as_text=True)[:2000])
        else:
            log.info("%s %s", request.method, request.full_path)

    @app.before_request
    def staff_only_admin():
        if request.path in admin_paths:
            user = auth.user_from_request()
            if user is None or user["role"] != "staff":
                abort(403)
            g.user = user

    @app.after_request
    def cors(resp):
        origin = request.headers.get("Origin")
        if origin:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Vary"] = "Origin"
            if app.config.get("CORS_ALLOW_CREDENTIALS"):
                resp.headers["Access-Control-Allow-Credentials"] = "true"
        return resp

    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def json_error(e):
        return jsonify(error=e.description), e.code

    @app.get("/health")
    def health():
        return {"ok": True}

    return app
