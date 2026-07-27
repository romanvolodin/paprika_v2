"""
Settings specific to production.
"""

from pathlib import Path

from environs import Env


env = Env()
env.read_env()

DEBUG = False

# Ideally this list stays empty: once Caddy serves frontend and backend
# from the same origin, the browser never needs CORS to begin with.
CORS_ALLOWED_ORIGINS: list[str] = []

PAPRIKA_DOMAIN = env.str("PAPRIKA_DOMAIN")

CSRF_TRUSTED_ORIGINS = [f"https://{PAPRIKA_DOMAIN}"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

STATIC_ROOT = Path("/var/lib/paprika/static")
MEDIA_ROOT = Path("/var/lib/paprika/media")
