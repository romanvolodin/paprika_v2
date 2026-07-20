"""
Settings specific to production.
"""

DEBUG = False

# Ideally this list stays empty: once Caddy serves frontend and backend
# from the same origin, the browser never needs CORS to begin with.
CORS_ALLOWED_ORIGINS: list[str] = []
