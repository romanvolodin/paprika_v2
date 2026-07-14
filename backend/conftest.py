"""Shared fixtures for the whole backend test suite.

Lives at the repo root (rather than inside a single app) so both
`apps/users/tests/` and `apps/auth/tests/` can use it, per the project's
test layout: unit/api tests live inside each app, but fixtures shared
across apps belong here.
"""

import json
import shutil
import tempfile

from django.test import Client
from django.test.client import BOUNDARY, encode_multipart
import pytest

from apps.users.tests.factories import DEFAULT_PASSWORD, UserFactory


@pytest.fixture(autouse=True)
def _tmp_media_root(settings):
    """Redirect MEDIA_ROOT to a throwaway directory for every test.

    Without this, avatar uploads in tests would land in the real
    `media/` folder used by local dev.
    """
    tmp_dir = tempfile.mkdtemp(prefix="paprika-test-media-")
    settings.MEDIA_ROOT = tmp_dir
    yield
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture(autouse=True, scope="session")
def _fast_password_hasher():
    """Use a fast, insecure password hasher for the whole test session.

    Tests hash a password on nearly every `UserFactory()` call - real
    deployment settings use a deliberately slow hasher, which adds up
    fast across a full test run. This is a one-line, visible override of
    a single setting for this process only - it doesn't fork the settings
    module the way a separate `settings/test.py` would, so `manage.py`
    and `pytest` still resolve every other setting identically.
    """
    from django.conf import settings as django_settings

    django_settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]


@pytest.fixture
def user_factory():
    """The `UserFactory` class itself, e.g. `user_factory(email=...)`."""
    return UserFactory


@pytest.fixture
def user(user_factory):
    """A single saved user with default field values."""
    return user_factory()


@pytest.fixture
def get_tokens(client):
    """Log in via the real `/api/v1/auth/login/` endpoint.

    Returns a callable so tests can request tokens for whichever
    email/password pair they need, e.g. after registering a second user.
    """

    def _get_tokens(email: str, password: str) -> dict:
        response = client.post(
            "/api/v1/auth/login/",
            data=json.dumps({"email": email, "password": password}),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        return response.json()

    return _get_tokens


@pytest.fixture
def auth_user(user_factory):
    """A user whose raw password is known (`DEFAULT_PASSWORD`), so it can log in."""
    return user_factory(password=DEFAULT_PASSWORD)


@pytest.fixture
def auth_client(auth_user, get_tokens):
    """A Django test client authenticated as `auth_user` with a real access token.

    Obtained through an actual `POST /api/v1/auth/login/` call (not minted by
    hand), so these tests exercise the exact same code path a real client
    would use.
    """
    tokens = get_tokens(auth_user.email, DEFAULT_PASSWORD)
    authed_client = Client()
    authed_client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {tokens['access_token']}"
    return authed_client


@pytest.fixture
def multipart_patch():
    """PATCH helper that reliably sends `multipart/form-data`.

    `Client.patch(path, data={...}, content_type=MULTIPART_CONTENT)` looks
    like it should work but silently drops every field under this stack
    (200 OK, nothing actually changes) - use this instead any time a test
    PATCHes `/users/<id>/`, since that endpoint always expects multipart.
    """

    def _patch(client, path, data):
        body = encode_multipart(BOUNDARY, data)
        return client.generic(
            "PATCH",
            path,
            data=body,
            content_type=f"multipart/form-data; boundary={BOUNDARY}",
        )

    return _patch
