import pytest


pytestmark = pytest.mark.django_db


class TestGetMe:
    def test_returns_the_authenticated_user(self, auth_client, auth_user):
        response = auth_client.get("/api/v1/users/me/")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == auth_user.id
        assert body["email"] == auth_user.email
        assert body["first_name"] == auth_user.first_name
        assert body["last_name"] == auth_user.last_name
        assert body["is_active"] is True
        assert body["avatar"] is None

    def test_requires_authentication(self, client):
        response = client.get("/api/v1/users/me/")

        assert response.status_code == 401

    def test_rejects_a_garbage_token(self, client):
        response = client.get(
            "/api/v1/users/me/",
            HTTP_AUTHORIZATION="Bearer not-a-real-jwt",
        )

        assert response.status_code == 401
