from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from apps.users.models import User


pytestmark = pytest.mark.django_db


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 100


class TestListUsers:
    def test_returns_all_users_paginated(self, auth_client, auth_user, user_factory):
        user_factory.create_batch(3)

        response = auth_client.get("/api/v1/users/")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 4  # auth_user + 3 created
        assert body["page"] == 1
        assert body["page_size"] == 20
        assert len(body["items"]) == 4

    def test_search_filters_by_email(self, auth_client, user_factory):
        user_factory(email="findme@example.com")
        user_factory(email="other@example.com")

        response = auth_client.get("/api/v1/users/?search=findme")

        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["email"] == "findme@example.com"

    def test_search_filters_by_first_or_last_name(self, auth_client, user_factory):
        user_factory(first_name="Zbigniew", last_name="Kowalski")
        user_factory(first_name="Jane", last_name="Zbrowska")
        user_factory(first_name="Someone", last_name="Else")

        response = auth_client.get("/api/v1/users/?search=zb")

        assert response.json()["total"] == 2

    def test_search_is_case_insensitive(self, auth_client, user_factory):
        user_factory(email="upper@example.com")

        response = auth_client.get("/api/v1/users/?search=UPPER")

        assert response.json()["total"] == 1

    def test_pagination_page_size_is_respected(self, auth_client, user_factory):
        user_factory.create_batch(5)

        response = auth_client.get("/api/v1/users/?page_size=2")

        body = response.json()
        assert len(body["items"]) == 2
        assert body["page_size"] == 2

    def test_page_out_of_range_is_clamped_to_the_last_page(
        self,
        auth_client,
        user_factory,
    ):
        # `Paginator.get_page()` clamps an out-of-range page number to the
        # last valid page instead of raising or returning an empty page.
        user_factory.create_batch(5)

        response = auth_client.get("/api/v1/users/?page=999&page_size=2")

        body = response.json()
        assert response.status_code == 200
        assert body["items"] != []
        assert (
            body["page"] == 999
        )  # echoes back the requested page, not the clamped one

    def test_page_size_over_max_is_rejected(self, auth_client):
        response = auth_client.get("/api/v1/users/?page_size=1000")

        assert response.status_code == 400

    def test_requires_authentication(self, client):
        response = client.get("/api/v1/users/")

        assert response.status_code == 401


class TestCreateUser:
    def test_creates_a_user_with_minimal_fields(self, auth_client):
        response = auth_client.post(
            "/api/v1/users/",
            data={
                "email": "newbie@example.com",
                "first_name": "New",
                "last_name": "Bie",
                "password": "PassW0rd1",
            },
        )

        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert body["email"] == "newbie@example.com"
        assert body["is_active"] is True
        assert body["avatar"] is None

        created = User.objects.get(email="newbie@example.com")
        assert created.check_password("PassW0rd1")

    def test_creates_a_user_without_password_as_unusable(self, auth_client):
        response = auth_client.post(
            "/api/v1/users/",
            data={
                "email": "invited@example.com",
                "first_name": "Invited",
                "last_name": "User",
            },
        )

        assert response.status_code == HTTPStatus.CREATED
        created = User.objects.get(email="invited@example.com")
        assert created.has_usable_password() is False

    def test_creates_a_user_with_an_avatar(self, auth_client):
        avatar = SimpleUploadedFile("avatar.png", PNG_BYTES, content_type="image/png")

        response = auth_client.post(
            "/api/v1/users/",
            data={
                "email": "withavatar@example.com",
                "first_name": "With",
                "last_name": "Avatar",
                "password": "PassW0rd1",
                "avatar": avatar,
            },
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.json()["avatar"] is not None
        assert response.json()["avatar"].endswith("avatar.png")

    def test_rejects_duplicate_email(self, auth_client, user_factory):
        existing = user_factory(email="taken@example.com")

        response = auth_client.post(
            "/api/v1/users/",
            data={
                "email": existing.email,
                "first_name": "Someone",
                "last_name": "Else",
                "password": "PassW0rd1",
            },
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_rejects_duplicate_email_case_insensitively(
        self,
        auth_client,
        user_factory,
    ):
        user_factory(email="taken@example.com")

        response = auth_client.post(
            "/api/v1/users/",
            data={
                "email": "TAKEN@example.com",
                "first_name": "Someone",
                "last_name": "Else",
                "password": "PassW0rd1",
            },
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_rejects_invalid_email_format(self, auth_client):
        response = auth_client.post(
            "/api/v1/users/",
            data={
                "email": "not-an-email",
                "first_name": "A",
                "last_name": "B",
                "password": "PassW0rd1",
            },
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_rejects_short_password(self, auth_client):
        response = auth_client.post(
            "/api/v1/users/",
            data={
                "email": "shortpass@example.com",
                "first_name": "A",
                "last_name": "B",
                "password": "short",
            },
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_rejects_missing_first_name(self, auth_client):
        response = auth_client.post(
            "/api/v1/users/",
            data={
                "email": "nofirst@example.com",
                "last_name": "B",
                "password": "PassW0rd1",
            },
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_rejects_avatar_with_disallowed_extension(self, auth_client):
        bad_file = SimpleUploadedFile(
            "avatar.txt",
            b"not an image",
            content_type="text/plain",
        )

        response = auth_client.post(
            "/api/v1/users/",
            data={
                "email": "badext@example.com",
                "first_name": "Bad",
                "last_name": "Ext",
                "password": "PassW0rd1",
                "avatar": bad_file,
            },
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_rejects_avatar_over_size_limit(self, auth_client):
        big_file = SimpleUploadedFile(
            "big.png",
            b"0" * (3 * 1024 * 1024),
            content_type="image/png",
        )

        response = auth_client.post(
            "/api/v1/users/",
            data={
                "email": "bigavatar@example.com",
                "first_name": "Big",
                "last_name": "Avatar",
                "password": "PassW0rd1",
                "avatar": big_file,
            },
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_requires_authentication(self, client):
        response = client.post(
            "/api/v1/users/",
            data={
                "email": "anon@example.com",
                "first_name": "A",
                "last_name": "B",
                "password": "PassW0rd1",
            },
        )

        assert response.status_code == 401
