import os

SECRET_KEY = "hf-shop-2f8a1c9e7b4d"
DATABASE = os.environ.get("SHOP_DB", os.path.join(os.path.dirname(__file__), "shop.db"))
TOKEN_HOURS = 12
PAYMENTS_URL = os.environ.get("PAYMENTS_URL", "https://api.payments.example/")
PAYMENTS_API_KEY = os.environ.get("PAYMENTS_API_KEY", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "whsec-local")
IMAGE_HOSTS = ["cdn.hartleyfinch.co.uk", "images.supplier-photos.com"]
IMAGE_DIR = os.environ.get("IMAGE_DIR", os.path.join(os.path.dirname(__file__), "images"))
CACHE_DIR = os.environ.get("CACHE_DIR", os.path.join(os.path.dirname(__file__), ".cache"))
CORS_ALLOW_CREDENTIALS = True
