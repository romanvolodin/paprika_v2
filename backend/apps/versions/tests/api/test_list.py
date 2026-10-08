from http import HTTPStatus

import pytest


pytestmark = pytest.mark.django_db


class TestListVersions:
    def test_returns_the_shots_versions_newest_first(
        self, auth_client, auth_user, shot, version_factory, project_membership_factory
    ):
        project_membership_factory(user=auth_user, project=shot.project)
        older = version_factory(shot=shot, name="PRJ_0010_v01")
        newer = version_factory(shot=shot, name="PRJ_0010_v04")
        version_factory()  # a version of some other shot

        response = auth_client.get(f"/api/v1/shots/{shot.id}/versions/")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert [item["id"] for item in body["items"]] == [newer.id, older.id]
        assert body["total"] == 2
        assert body["page"] == 1
        assert body["page_size"] == 20

    def test_item_shape(
        self, auth_client, auth_user, shot, version_factory, project_membership_factory
    ):
        project_membership_factory(user=auth_user, project=shot.project)
        version_factory(shot=shot, name="PRJ_0010_v01", created_by=auth_user)

        item = auth_client.get(f"/api/v1/shots/{shot.id}/versions/").json()["items"][0]

        assert item["name"] == "PRJ_0010_v01"
        assert item["type"] == "image"
        assert item["shot_id"] == shot.id
        assert item["project_id"] == shot.project_id
        assert item["source"].startswith("http")
        assert item["thumb"].startswith("http")
        assert item["converted"] is None
        assert item["duration"] is None
        assert item["fps"] is None
        assert item["codec"] == ""
        assert item["created_by"]["id"] == auth_user.id

    def test_paginates(
        self, auth_client, auth_user, shot, version_factory, project_membership_factory
    ):
        project_membership_factory(user=auth_user, project=shot.project)
        for _ in range(3):
            version_factory(shot=shot)

        body = auth_client.get(
            f"/api/v1/shots/{shot.id}/versions/?page=2&page_size=2"
        ).json()

        assert len(body["items"]) == 1
        assert body["total"] == 3
        assert body["page"] == 2

    def test_search_filters_by_name_case_insensitively(
        self, auth_client, auth_user, shot, version_factory, project_membership_factory
    ):
        project_membership_factory(user=auth_user, project=shot.project)
        wanted = version_factory(shot=shot, name="PRJ_0010_v04")
        version_factory(shot=shot, name="PRJ_0010_v01")

        body = auth_client.get(f"/api/v1/shots/{shot.id}/versions/?search=v04").json()

        assert [item["id"] for item in body["items"]] == [wanted.id]
        assert body["total"] == 1

    def test_empty_shot_returns_an_empty_page(
        self, auth_client, auth_user, shot, project_membership_factory
    ):
        project_membership_factory(user=auth_user, project=shot.project)

        body = auth_client.get(f"/api/v1/shots/{shot.id}/versions/").json()

        assert body["items"] == []
        assert body["total"] == 0

    def test_read_only_client_can_list(
        self, auth_client, auth_user, shot, version_factory, project_membership_factory
    ):
        project_membership_factory(user=auth_user, project=shot.project, role="client")
        version_factory(shot=shot)

        response = auth_client.get(f"/api/v1/shots/{shot.id}/versions/")

        assert response.status_code == HTTPStatus.OK

    def test_non_member_gets_a_404(self, auth_client, shot, project_membership_factory):
        project_membership_factory(project=shot.project)  # some other user

        response = auth_client.get(f"/api/v1/shots/{shot.id}/versions/")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_requires_authentication(self, client, shot):
        response = client.get(f"/api/v1/shots/{shot.id}/versions/")

        assert response.status_code == HTTPStatus.UNAUTHORIZED
