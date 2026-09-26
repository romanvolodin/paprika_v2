import json

from django.test import Client
import pytest

from apps.users.tests.factories import DEFAULT_PASSWORD


pytestmark = pytest.mark.django_db


def _login(client, user):
    response = client.post(
        "/api/v1/auth/login/",
        data=json.dumps({"email": user.email, "password": DEFAULT_PASSWORD}),
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    return response


def _refresh(client):
    # No body: the browser sends the refresh cookie on its own.
    return client.post("/api/v1/auth/refresh/")


class TestRefreshSuccess:
    def test_returns_the_authenticated_user(self, client, auth_user):
        _login(client, auth_user)

        response = _refresh(client)

        assert response.status_code == 200
        assert response.json()["email"] == auth_user.email

    def test_rotates_both_cookies(self, client, auth_user):
        login_response = _login(client, auth_user)
        old_access = login_response.cookies["access_token"].value
        old_refresh = login_response.cookies["refresh_token"].value

        response = _refresh(client)

        assert response.cookies["access_token"].value != old_access
        assert response.cookies["refresh_token"].value != old_refresh

    def test_new_access_cookie_works_on_protected_endpoint(self, client, auth_user):
        _login(client, auth_user)
        _refresh(client)

        response = client.get("/api/v1/users/me/")

        assert response.status_code == 200


class TestRefreshFailure:
    def test_no_refresh_cookie_at_all_is_rejected(self, client):
        response = _refresh(client)

        assert response.status_code == 401

    def test_garbage_refresh_cookie_is_rejected(self, client):
        client.cookies["refresh_token"] = "not-a-real-jwt"

        response = _refresh(client)

        assert response.status_code == 401

    def test_access_token_cannot_be_used_to_refresh(self, client, auth_user):
        _login(client, auth_user)
        # Swap in the access token where the refresh token is expected.
        client.cookies["refresh_token"] = client.cookies["access_token"].value

        response = _refresh(client)

        assert response.status_code == 401

    def test_refresh_still_works_after_logout_since_only_the_access_token_is_revoked(
        self,
        client,
        auth_user,
    ):
        # The refresh cookie is scoped to this endpoint's path alone, so
        # a real browser never sends it to `/auth/logout/` - logout can
        # only revoke the access token used to authenticate that call.
        # This is the accepted trade-off, not a bug: see
        # `REFRESH_COOKIE_PATH` in `apps/auth/api/views.py`.
        #
        # Django's test `Client` can't simulate this: its cookie jar
        # ignores `path` entirely, so it would resend the refresh cookie
        # to `/auth/logout/` too, and then drop it once that response's
        # discard `Set-Cookie` reaches it - something a real browser
        # would never do. A second client that only carries the access
        # token stands in for what a browser actually sends to logout.
        login_response = _login(client, auth_user)
        logout_client = Client()
        logout_client.cookies["access_token"] = login_response.cookies[
            "access_token"
        ].value
        logout_response = logout_client.post("/api/v1/auth/logout/")
        assert logout_response.status_code == 204

        response = _refresh(client)

        assert response.status_code == 200
