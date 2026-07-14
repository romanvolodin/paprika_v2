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


def _refresh(client, refresh_token):
    return client.post(
        "/api/v1/auth/refresh/",
        data=json.dumps({"refresh_token": refresh_token}),
        content_type="application/json",
    )


class TestRefreshSuccess:
    def test_returns_a_brand_new_token_pair(self, client, auth_user):
        tokens = _login(client, auth_user)

        response = _refresh(client, tokens["refresh_token"])

        assert response.status_code == 200
        new_tokens = response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens

    def test_new_access_token_works_on_protected_endpoint(self, client, auth_user):
        tokens = _login(client, auth_user)
        new_tokens = _refresh(client, tokens["refresh_token"]).json()

        response = client.get(
            "/api/v1/users/me/",
            HTTP_AUTHORIZATION=f"Bearer {new_tokens['access_token']}",
        )

        assert response.status_code == 200


class TestRefreshFailure:
    def test_garbage_token_is_rejected(self, client):
        response = _refresh(client, "not-a-real-jwt")

        assert response.status_code == 401

    def test_access_token_cannot_be_used_to_refresh(self, client, auth_user):
        tokens = _login(client, auth_user)

        response = _refresh(client, tokens["access_token"])

        assert response.status_code == 401

    def test_revoked_refresh_token_is_rejected_after_logout(self, client, auth_user):
        tokens = _login(client, auth_user)
        client.post(
            "/api/v1/auth/logout/",
            data=json.dumps({"refresh_token": tokens["refresh_token"]}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}",
        )

        response = _refresh(client, tokens["refresh_token"])

        assert response.status_code == 401

    def test_missing_refresh_token_is_a_validation_error(self, client):
        response = client.post(
            "/api/v1/auth/refresh/",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 400
