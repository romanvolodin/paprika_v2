from http import HTTPStatus

import pytest


pytestmark = pytest.mark.django_db


@pytest.fixture
def member_project(auth_user, project, project_membership_factory):
    project_membership_factory(user=auth_user, project=project)
    return project


def _type(project, abbreviation):
    return project.company.task_types.get(abbreviation=abbreviation)


class TestFilterShotsByTaskType:
    def test_project_list_returns_only_shots_with_a_task_of_that_type(
        self, auth_client, member_project, shot_factory, task_factory, shot_task_factory
    ):
        cleanup, comp = _type(member_project, "CLN"), _type(member_project, "COMP")
        with_cleanup = shot_factory(project=member_project)
        with_comp = shot_factory(project=member_project)
        shot_factory(project=member_project)  # no tasks at all
        shot_task_factory(
            shot=with_cleanup, task=task_factory(project=member_project, type=cleanup)
        )
        shot_task_factory(
            shot=with_comp, task=task_factory(project=member_project, type=comp)
        )

        response = auth_client.get(
            f"/api/v1/projects/{member_project.id}/shots/?task_type={cleanup.id}"
        )

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert [i["id"] for i in body["items"]] == [with_cleanup.id]
        assert body["total"] == 1

    def test_a_shot_with_several_tasks_of_the_type_is_listed_once(
        self, auth_client, member_project, shot_factory, task_factory, shot_task_factory
    ):
        cleanup = _type(member_project, "CLN")
        shot = shot_factory(project=member_project)
        for _ in range(3):
            shot_task_factory(
                shot=shot, task=task_factory(project=member_project, type=cleanup)
            )

        body = auth_client.get(
            f"/api/v1/projects/{member_project.id}/shots/?task_type={cleanup.id}"
        ).json()

        assert [i["id"] for i in body["items"]] == [shot.id]
        assert body["total"] == 1

    def test_group_list_supports_the_filter_too(
        self,
        auth_client,
        member_project,
        shot_group_factory,
        shot_factory,
        task_factory,
        shot_task_factory,
    ):
        cleanup = _type(member_project, "CLN")
        group = shot_group_factory(project=member_project)
        match = shot_factory(project=member_project, groups=[group])
        shot_factory(project=member_project, groups=[group])
        shot_task_factory(
            shot=match, task=task_factory(project=member_project, type=cleanup)
        )

        response = auth_client.get(
            f"/api/v1/shot-groups/{group.id}/shots/?task_type={cleanup.id}"
        )

        assert [i["id"] for i in response.json()["items"]] == [match.id]

    def test_combines_with_search(
        self, auth_client, member_project, shot_factory, task_factory, shot_task_factory
    ):
        cleanup = _type(member_project, "CLN")
        wanted = shot_factory(project=member_project, name="PRJ_0010")
        other = shot_factory(project=member_project, name="PRJ_0020")
        for shot in (wanted, other):
            shot_task_factory(
                shot=shot, task=task_factory(project=member_project, type=cleanup)
            )

        body = auth_client.get(
            f"/api/v1/projects/{member_project.id}/shots/"
            f"?task_type={cleanup.id}&search=0010"
        ).json()

        assert [i["id"] for i in body["items"]] == [wanted.id]

    def test_an_unknown_type_returns_no_shots(
        self, auth_client, member_project, shot_factory
    ):
        shot_factory(project=member_project)

        body = auth_client.get(
            f"/api/v1/projects/{member_project.id}/shots/?task_type=999999"
        ).json()

        assert body["items"] == []

    def test_without_the_filter_every_shot_is_listed(
        self, auth_client, member_project, shot_factory
    ):
        shot_factory(project=member_project)
        shot_factory(project=member_project)

        body = auth_client.get(f"/api/v1/projects/{member_project.id}/shots/").json()

        assert body["total"] == 2
