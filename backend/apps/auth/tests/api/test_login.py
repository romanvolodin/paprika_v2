import json

import pytest

from apps.users.tests.factories import DEFAULT_PASSWORD


pytestmark = pytest.mark.django_db


def _login(client, **payload):
    return client.post(
        "/api/v1/auth/login/",
        data=json.dumps(payload),
        content_type="application/json",
    )


class TestLoginSuccess:
    def test_returns_access_and_refresh_tokens(self, client, auth_user):
        response = _login(client, email=auth_user.email, password=DEFAULT_PASSWORD)

        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body

    def test_access_token_can_be_used_on_protected_endpoint(self, client, auth_user):
        tokens = _login(client, email=auth_user.email, password=DEFAULT_PASSWORD).json()

        response = client.get(
            "/api/v1/users/me/",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}",
        )

        assert response.status_code == 200
        assert response.json()["email"] == auth_user.email


class TestLoginFailure:
    def test_wrong_password_is_rejected(self, client, auth_user):
        response = _login(client, email=auth_user.email, password="wrong-password")

        assert response.status_code == 401

    def test_unknown_email_is_rejected(self, client):
        response = _login(client, email="nobody@example.com", password="whatever123")

        assert response.status_code == 401

    def test_inactive_user_cannot_log_in(self, client, user_factory):
        inactive_user = user_factory(is_active=False, password=DEFAULT_PASSWORD)

        response = _login(
            client,
            email=inactive_user.email,
            password=DEFAULT_PASSWORD,
        )

        assert response.status_code == 401

    def test_is_case_sensitive_on_email(self, client, auth_user):
        # `ModelBackend`/`BaseUserManager.get_by_natural_key` do an exact
        # match on `email` - there's no `iexact` lookup for login, unlike
        # the create-user duplicate-email check.
        response = _login(
            client,
            email=auth_user.email.upper(),
            password=DEFAULT_PASSWORD,
        )

        assert response.status_code == 401

    def test_missing_password_is_a_validation_error(self, client, auth_user):
        response = _login(client, email=auth_user.email)

        assert response.status_code == 400

    def test_missing_email_is_a_validation_error(self, client):
        response = _login(client, password="whatever123")

        assert response.status_code == 400
