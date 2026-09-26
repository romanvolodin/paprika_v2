"""
Settings specific to development.
"""

DEBUG = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# The Vite dev server and Django run on different ports, so the browser
# treats API calls as cross-origin. Auth now rides on cookies, so the
# preflight response needs to allow credentials, or the browser won't
# store or send them at all.
CORS_ALLOW_CREDENTIALS = True
