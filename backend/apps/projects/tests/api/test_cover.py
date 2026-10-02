from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
import pytest


pytestmark = pytest.mark.django_db


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 100


def _png(name="cover.png"):
    return SimpleUploadedFile(name, PNG_BYTES, content_type="image/png")


class TestCoverUploadOnUpdate:
    def test_attaches_a_cover_to_a_project_with_none(
        self,
        auth_client,
        auth_user,
        multipart_patch,
        project_factory,
        project_membership_factory,
    ):
        project = project_factory()
        project_membership_factory(user=auth_user, project=project)
        assert not project.cover

        response = multipart_patch(
            auth_client,
            f"/api/v1/projects/{project.id}/",
            {"cover": _png()},
        )

        assert response.status_code == 200
        assert response.json()["cover"] is not None
        project.refresh_from_db()
        assert project.cover

    def test_replaces_an_existing_cover(
        self,
        auth_client,
        auth_user,
        multipart_patch,
        project_factory,
        project_membership_factory,
    ):
        project = project_factory()
        project_membership_factory(user=auth_user, project=project)
        multipart_patch(
            auth_client,
            f"/api/v1/projects/{project.id}/",
            {"cover": _png("first.png")},
        )
        project.refresh_from_db()
        old_cover_name = project.cover.name

        response = multipart_patch(
            auth_client,
            f"/api/v1/projects/{project.id}/",
            {"cover": _png("second.png")},
        )

        assert response.status_code == 200
        project.refresh_from_db()
        assert project.cover.name != old_cover_name
        assert not project.cover.storage.exists(old_cover_name)

    def test_remove_cover_flag_clears_it(
        self,
        auth_client,
        auth_user,
        multipart_patch,
        project_factory,
        project_membership_factory,
    ):
        project = project_factory()
        project_membership_factory(user=auth_user, project=project)
        multipart_patch(
            auth_client,
            f"/api/v1/projects/{project.id}/",
            {"cover": _png()},
        )
        project.refresh_from_db()
        old_cover_name = project.cover.name

        response = multipart_patch(
            auth_client,
            f"/api/v1/projects/{project.id}/",
            {"remove_cover": "true"},
        )

        assert response.status_code == 200
        assert response.json()["cover"] is None
        project.refresh_from_db()
        assert not project.cover
        assert not project.cover.storage.exists(old_cover_name)

    def test_remove_cover_flag_is_a_noop_when_there_is_none(
        self,
        auth_client,
        auth_user,
        multipart_patch,
        project_factory,
        project_membership_factory,
    ):
        project = project_factory()
        project_membership_factory(user=auth_user, project=project)

        response = multipart_patch(
            auth_client,
            f"/api/v1/projects/{project.id}/",
            {"remove_cover": "true"},
        )

        assert response.status_code == 200
        assert response.json()["cover"] is None

    def test_new_cover_file_takes_priority_over_remove_flag(
        self,
        auth_client,
        auth_user,
        multipart_patch,
        project_factory,
        project_membership_factory,
    ):
        # Per the endpoint's documented behavior: `remove_cover` is
        # ignored if a new `cover` file is also sent in the same request.
        project = project_factory()
        project_membership_factory(user=auth_user, project=project)

        response = multipart_patch(
            auth_client,
            f"/api/v1/projects/{project.id}/",
            {"cover": _png(), "remove_cover": "true"},
        )

        assert response.status_code == 200
        assert response.json()["cover"] is not None

    def test_rejects_disallowed_extension(
        self,
        auth_client,
        auth_user,
        multipart_patch,
        project_factory,
        project_membership_factory,
    ):
        project = project_factory()
        project_membership_factory(user=auth_user, project=project)
        bad_file = SimpleUploadedFile(
            "cover.txt",
            b"not an image",
            content_type="text/plain",
        )

        response = multipart_patch(
            auth_client,
            f"/api/v1/projects/{project.id}/",
            {"cover": bad_file},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        project.refresh_from_db()
        assert not project.cover

    def test_rejects_oversized_file(
        self,
        auth_client,
        auth_user,
        multipart_patch,
        project_factory,
        project_membership_factory,
    ):
        project = project_factory()
        project_membership_factory(user=auth_user, project=project)
        big_file = SimpleUploadedFile(
            "big.png",
            b"0" * (6 * 1024 * 1024),
            content_type="image/png",
        )

        response = multipart_patch(
            auth_client,
            f"/api/v1/projects/{project.id}/",
            {"cover": big_file},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_non_member_gets_404(
        self,
        auth_client,
        multipart_patch,
        project_factory,
        project_membership_factory,
    ):
        project = project_factory()
        project_membership_factory(project=project)  # some other user

        response = multipart_patch(
            auth_client,
            f"/api/v1/projects/{project.id}/",
            {"cover": _png()},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
