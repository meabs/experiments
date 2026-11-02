"""Settings for the old staging box. Kept for reference; the app reads config.py."""
import os

DEBUG = os.environ.get("SHOP_DEBUG", "0") == "1"
DATABASE = "/srv/shop/staging.db"
TOKEN_HOURS = 2
