import json

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


def _logout(client):
    # No body: the access token cookie identifies who's logging out.
    return client.post("/api/v1/auth/logout/")


class TestLogoutSuccess:
    def test_returns_no_content(self, client, auth_user):
        _login(client, auth_user)

        response = _logout(client)

        assert response.status_code == 204

    def test_drops_both_cookies(self, client, auth_user):
        _login(client, auth_user)

        response = _logout(client)

        assert response.cookies["access_token"].value == ""
        assert response.cookies["refresh_token"].value == ""

    def test_access_token_is_revoked_and_cannot_be_reused(self, client, auth_user):
        _login(client, auth_user)
        _logout(client)

        response = client.get("/api/v1/users/me/")

        assert response.status_code == 401


class TestLogoutFailure:
    def test_requires_authentication(self, client):
        response = _logout(client)

        assert response.status_code == 401

    def test_already_revoked_access_token_cannot_log_out_again(
        self,
        client,
        auth_user,
    ):
        _login(client, auth_user)
        _logout(client)

        response = _logout(client)

        assert response.status_code == 401
