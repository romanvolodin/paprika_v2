"""
Entry point for Django settings, built with `django-split-settings`.

Environment selection works like this:

- `DJANGO_ENV` (a real OS environment variable - see note below) picks
  which file under `environments/` gets included: `development` or
  `production`. This controls *code-level* differences between environments
  (debug flags, security headers, etc.) - it is decided at deploy/build
  time, not a secret.
- `.env` (one file, gitignored, see `.env.template`) holds the actual
  secrets/config values for wherever this happens to be running - the
  local dev machine, CI, or a production server. There is only ever one
  `.env` file on any given machine; its *contents* differ per machine,
  its *name* never does. `components/common.py` reads it via `environs`.
- `environments/local.py` (optional, gitignored, see `local.py.template`)
  lets a single developer override anything for their own machine only,
  without touching files anyone else's setup depends on.

IMPORTANT: `DJANGO_ENV` must be set as a real environment variable
(e.g. `DJANGO_ENV=production python manage.py runserver`, or `ENV
DJANGO_ENV=production` baked into a Docker image) - NOT inside `.env`.
`.env` is only read once `components/common.py` is included below, which
happens *after* `DJANGO_ENV` has already been used to pick this list of
files, so a value placed in `.env` would arrive too late to have any
effect here.
"""

import os

from split_settings.tools import include, optional


os.environ.setdefault("DJANGO_ENV", "development")
_ENV = os.environ["DJANGO_ENV"]

include(
    "components/api.py",
    "components/common.py",
    f"environments/{_ENV}.py",
    optional("environments/local.py"),
)
