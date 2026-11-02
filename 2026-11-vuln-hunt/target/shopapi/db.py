import sqlite3

import click
from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'customer',
    reset_token TEXT, reset_expires TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY, sku TEXT UNIQUE NOT NULL, name TEXT NOT NULL, price_pence INTEGER NOT NULL,
    description_md TEXT NOT NULL DEFAULT '', stock INTEGER NOT NULL DEFAULT 0, image TEXT);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES users(id), status TEXT NOT NULL,
    total_pence INTEGER NOT NULL, paid_pence INTEGER NOT NULL DEFAULT 0, payment_id TEXT,
    delivered_on TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id), sku TEXT NOT NULL,
    qty INTEGER NOT NULL, price_pence INTEGER NOT NULL,
    cancelled_qty INTEGER NOT NULL DEFAULT 0, returned_qty INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS refunds (
    id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id), amount_pence INTEGER NOT NULL,
    kind TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS giftcards (
    code TEXT PRIMARY KEY, balance_pence INTEGER NOT NULL, owner_id INTEGER REFERENCES users(id));
CREATE TABLE IF NOT EXISTS giftcard_redemptions (
    id INTEGER PRIMARY KEY, code TEXT NOT NULL, order_id INTEGER NOT NULL, amount_pence INTEGER NOT NULL,
    created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id),
    author_id INTEGER NOT NULL REFERENCES users(id), author_name TEXT NOT NULL, rating INTEGER NOT NULL,
    body TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY, actor_id INTEGER, action TEXT NOT NULL, detail TEXT,
    created TEXT DEFAULT CURRENT_TIMESTAMP);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    get_db().executescript(SCHEMA)


@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("Initialised the database.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
