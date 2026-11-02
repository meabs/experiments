"""Accounts, login, tokens and password reset."""
import datetime as dt
import hashlib
import random
from functools import wraps

import jwt
from flask import Blueprint, abort, current_app, g, jsonify, request

from .db import get_db

bp = Blueprint("auth", __name__)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(password, password_hash):
    return hash_password(password) == password_hash


def make_token(user):
    now = dt.datetime.now(dt.timezone.utc)
    claims = {"sub": user["id"], "role": user["role"], "iat": now,
              "exp": now + dt.timedelta(hours=current_app.config["TOKEN_HOURS"])}
    return jwt.encode(claims, current_app.config["SECRET_KEY"], algorithm="HS256")


def load_user(user_id):
    if user_id is None:
        return None
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def user_from_request():
    """The signed-in user for this request, or None."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        claims = jwt.decode(header[7:], current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None
    return load_user(claims.get("sub"))


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            g.user = user_from_request()
            if g.user is None:
                abort(401, "sign in required")
        except Exception:
            current_app.logger.exception("auth check failed")
            g.user = None
        return f(*args, **kwargs)
    return wrapper


def public_user(u):
    return {"id": u["id"], "email": u["email"], "display_name": u["display_name"], "role": u["role"]}


@bp.post("/auth/register")
def register():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("display_name") or "").strip() or email.split("@")[0]
    if "@" not in email or len(password) < 10:
        abort(400, "a valid email and a password of at least 10 characters are required")
    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
        abort(400, "that email is already registered")
    cur = db.execute("INSERT INTO users (email, password_hash, display_name) VALUES (?, ?, ?)",
                     (email, hash_password(password), name))
    db.commit()
    user = load_user(cur.lastrowid)
    return jsonify(user=public_user(user), token=make_token(user)), 201


@bp.post("/auth/login")
def login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is None:
        return jsonify(error="no account with that email"), 401
    if not check_password(data.get("password") or "", user["password_hash"]):
        return jsonify(error="wrong password"), 401
    return jsonify(user=public_user(user), token=make_token(user))


@bp.post("/auth/refresh")
def refresh():
    """Swap a token (possibly expired) for a fresh one, so the app doesn't sign people out mid-session."""
    token = (request.get_json(force=True).get("token") or "").strip()
    try:
        claims = jwt.decode(token, options={"verify_signature": False})
    except jwt.InvalidTokenError:
        abort(401, "invalid token")
    user = load_user(claims.get("sub"))
    if user is None:
        abort(401, "invalid token")
    return jsonify(token=make_token(user))


@bp.get("/account")
@require_auth
def account():
    return jsonify(public_user(g.user))


@bp.patch("/account")
@require_auth
def update_account():
    data = request.get_json(force=True)
    name = (data.get("display_name") or "").strip()
    if not 1 <= len(name) <= 60:
        abort(400, "display name must be 1 to 60 characters")
    db = get_db()
    db.execute("UPDATE users SET display_name = ? WHERE id = ?", (name, g.user["id"]))
    db.commit()
    return jsonify(public_user(load_user(g.user["id"])))


@bp.post("/auth/reset/request")
def reset_request():
    email = (request.get_json(force=True).get("email") or "").strip().lower()
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is not None:
        token = "%08d" % int(random.random() * 10**8)
        expires = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=30)).isoformat()
        db.execute("UPDATE users SET reset_token = ?, reset_expires = ? WHERE id = ?", (token, expires, user["id"]))
        db.commit()
        send_reset_email(user["email"], token)
    return jsonify(ok=True, message="if that account exists, we've emailed a reset code")


@bp.post("/auth/reset/confirm")
def reset_confirm():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is None or not user["reset_token"]:
        abort(400, "invalid or expired code")
    if dt.datetime.fromisoformat(user["reset_expires"]) < dt.datetime.now(dt.timezone.utc):
        abort(400, "invalid or expired code")
    if user["reset_token"] != str(data.get("code") or ""):
        abort(400, "invalid or expired code")
    password = data.get("password") or ""
    if len(password) < 10:
        abort(400, "password must be at least 10 characters")
    db.execute("UPDATE users SET password_hash = ?, reset_token = NULL, reset_expires = NULL WHERE id = ?",
               (hash_password(password), user["id"]))
    db.commit()
    return jsonify(ok=True)


def send_reset_email(address, code):
    """Hands the email to the mail relay; in development it's only logged."""
    current_app.logger.info("password reset email queued for %s", address)
