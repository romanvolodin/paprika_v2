from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
import pytest


pytestmark = pytest.mark.django_db


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 100


def _png(name="avatar.png"):
    return SimpleUploadedFile(name, PNG_BYTES, content_type="image/png")


class TestAvatarUploadOnUpdate:
    def test_attaches_an_avatar_to_a_user_with_none(
        self,
        auth_client,
        multipart_patch,
        user_factory,
    ):
        target = user_factory()
        assert not target.avatar

        response = multipart_patch(
            auth_client,
            f"/api/v1/users/{target.id}/",
            {"avatar": _png()},
        )

        assert response.status_code == 200
        assert response.json()["avatar"] is not None
        target.refresh_from_db()
        assert target.avatar

    def test_replaces_an_existing_avatar(
        self,
        auth_client,
        multipart_patch,
        user_factory,
    ):
        target = user_factory()
        multipart_patch(
            auth_client,
            f"/api/v1/users/{target.id}/",
            {"avatar": _png("first.png")},
        )
        target.refresh_from_db()
        old_avatar_name = target.avatar.name

        response = multipart_patch(
            auth_client,
            f"/api/v1/users/{target.id}/",
            {"avatar": _png("second.png")},
        )

        assert response.status_code == 200
        target.refresh_from_db()
        assert target.avatar.name != old_avatar_name
        assert not target.avatar.storage.exists(old_avatar_name)

    def test_remove_avatar_flag_clears_it(
        self,
        auth_client,
        multipart_patch,
        user_factory,
    ):
        target = user_factory()
        multipart_patch(
            auth_client,
            f"/api/v1/users/{target.id}/",
            {"avatar": _png()},
        )
        target.refresh_from_db()
        old_avatar_name = target.avatar.name

        response = multipart_patch(
            auth_client,
            f"/api/v1/users/{target.id}/",
            {"remove_avatar": "true"},
        )

        assert response.status_code == 200
        assert response.json()["avatar"] is None
        target.refresh_from_db()
        assert not target.avatar
        assert not target.avatar.storage.exists(old_avatar_name)

    def test_remove_avatar_flag_is_a_noop_when_there_is_none(
        self,
        auth_client,
        multipart_patch,
        user_factory,
    ):
        target = user_factory()

        response = multipart_patch(
            auth_client,
            f"/api/v1/users/{target.id}/",
            {"remove_avatar": "true"},
        )

        assert response.status_code == 200
        assert response.json()["avatar"] is None

    def test_new_avatar_file_takes_priority_over_remove_flag(
        self,
        auth_client,
        multipart_patch,
        user_factory,
    ):
        # Per the endpoint's documented behavior: `remove_avatar` is
        # ignored if a new `avatar` file is also sent in the same request.
        target = user_factory()

        response = multipart_patch(
            auth_client,
            f"/api/v1/users/{target.id}/",
            {"avatar": _png(), "remove_avatar": "true"},
        )

        assert response.status_code == 200
        assert response.json()["avatar"] is not None

    def test_rejects_disallowed_extension(
        self,
        auth_client,
        multipart_patch,
        user_factory,
    ):
        target = user_factory()
        bad_file = SimpleUploadedFile(
            "avatar.txt",
            b"not an image",
            content_type="text/plain",
        )

        response = multipart_patch(
            auth_client,
            f"/api/v1/users/{target.id}/",
            {"avatar": bad_file},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        target.refresh_from_db()
        assert not target.avatar

    def test_rejects_oversized_file(self, auth_client, multipart_patch, user_factory):
        target = user_factory()
        big_file = SimpleUploadedFile(
            "big.png",
            b"0" * (3 * 1024 * 1024),
            content_type="image/png",
        )

        response = multipart_patch(
            auth_client,
            f"/api/v1/users/{target.id}/",
            {"avatar": big_file},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
