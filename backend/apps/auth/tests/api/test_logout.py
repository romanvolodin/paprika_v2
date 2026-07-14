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
    return response.json()


def _logout(client, access_token, refresh_token=None):
    payload = {"refresh_token": refresh_token} if refresh_token else {}
    return client.post(
        "/api/v1/auth/logout/",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {access_token}",
    )


class TestLogoutSuccess:
    def test_returns_a_confirmation_message(self, client, auth_user):
        tokens = _login(client, auth_user)

        response = _logout(client, tokens["access_token"])

        assert response.status_code == 200
        assert response.json()["detail"]

    def test_access_token_is_revoked_and_cannot_be_reused(self, client, auth_user):
        tokens = _login(client, auth_user)
        _logout(client, tokens["access_token"])

        response = client.get(
            "/api/v1/users/me/",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}",
        )

        assert response.status_code == 401

    def test_paired_refresh_token_is_revoked_when_provided(self, client, auth_user):
        tokens = _login(client, auth_user)
        _logout(client, tokens["access_token"], refresh_token=tokens["refresh_token"])

        response = client.post(
            "/api/v1/auth/refresh/",
            data=json.dumps({"refresh_token": tokens["refresh_token"]}),
            content_type="application/json",
        )

        assert response.status_code == 401

    def test_refresh_token_stays_valid_if_not_provided_at_logout(
        self,
        client,
        auth_user,
    ):
        tokens = _login(client, auth_user)
        _logout(client, tokens["access_token"])  # no refresh_token passed

        response = client.post(
            "/api/v1/auth/refresh/",
            data=json.dumps({"refresh_token": tokens["refresh_token"]}),
            content_type="application/json",
        )

        assert response.status_code == 200

    def test_garbage_refresh_token_at_logout_is_ignored_not_an_error(
        self,
        client,
        auth_user,
    ):
        tokens = _login(client, auth_user)

        response = _logout(
            client,
            tokens["access_token"],
            refresh_token="not-a-real-jwt",
        )

        assert response.status_code == 200


class TestLogoutFailure:
    def test_requires_authentication(self, client):
        response = client.post(
            "/api/v1/auth/logout/",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 401

    def test_already_revoked_access_token_cannot_log_out_again(
        self,
        client,
        auth_user,
    ):
        tokens = _login(client, auth_user)
        _logout(client, tokens["access_token"])

        response = _logout(client, tokens["access_token"])

        assert response.status_code == 401
