"""System messages created by the versions and tasks API handlers."""

from http import HTTPStatus
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from apps.chat.models import Message
from apps.chat.tests.api.conftest import patch_json, post_json
from apps.versions.tests.conftest import make_jpeg


pytestmark = pytest.mark.django_db


def _system(shot):
    return list(Message.objects.filter(shot=shot, type=Message.Type.SYSTEM))


def _status(project, name):
    return project.company.task_statuses.get(name=name)


class TestVersionUploaded:
    def test_an_upload_records_an_event_linked_to_the_version(
        self, auth_client, auth_user, member_shot
    ):
        response = auth_client.post(
            f"/api/v1/shots/{member_shot.id}/versions/",
            {"source": SimpleUploadedFile("PRJ_0010_v01.jpg", make_jpeg())},
        )

        assert response.status_code == HTTPStatus.CREATED, response.content
        (message,) = _system(member_shot)
        assert message.event == "version_uploaded"
        assert message.created_by == auth_user
        assert message.payload == {
            "version_id": response.json()["id"],
            "version_name": "PRJ_0010_v01",
        }
        assert [v.id for v in message.versions.all()] == [response.json()["id"]]

    def test_the_event_is_in_the_chat_with_the_version(self, auth_client, member_shot):
        auth_client.post(
            f"/api/v1/shots/{member_shot.id}/versions/",
            {"source": SimpleUploadedFile("PRJ_0010_v01.jpg", make_jpeg())},
        )

        item = auth_client.get(f"/api/v1/shots/{member_shot.id}/chat/").json()["items"][
            0
        ]

        assert item["event"] == "version_uploaded"
        assert item["versions"][0]["name"] == "PRJ_0010_v01"

    def test_a_rejected_upload_records_nothing(
        self, auth_client, member_shot, version_factory
    ):
        version_factory(shot=member_shot, name="PRJ_0010_v01")

        response = auth_client.post(
            f"/api/v1/shots/{member_shot.id}/versions/",
            {"source": SimpleUploadedFile("PRJ_0010_v01.jpg", make_jpeg())},
        )

        assert response.status_code == HTTPStatus.CONFLICT
        assert _system(member_shot) == []

    def test_a_failed_event_rolls_the_version_back(self, auth_client, member_shot):
        with mock.patch(
            "apps.versions.api.views.record_version_uploaded",
            side_effect=RuntimeError("boom"),
        ):
            with pytest.raises(RuntimeError):
                auth_client.post(
                    f"/api/v1/shots/{member_shot.id}/versions/",
                    {"source": SimpleUploadedFile("PRJ_0010_v01.jpg", make_jpeg())},
                )

        from apps.versions.models import Version

        assert not Version.objects.exists()

    def test_deleting_the_version_keeps_the_event_readable(
        self, auth_client, member_shot
    ):
        response = auth_client.post(
            f"/api/v1/shots/{member_shot.id}/versions/",
            {"source": SimpleUploadedFile("PRJ_0010_v01.jpg", make_jpeg())},
        )
        auth_client.delete(f"/api/v1/versions/{response.json()['id']}/")

        item = auth_client.get(f"/api/v1/shots/{member_shot.id}/chat/").json()["items"][
            0
        ]

        assert item["versions"] == []
        assert item["payload"]["version_name"] == "PRJ_0010_v01"


class TestTaskAdded:
    def test_placing_a_task_records_an_event(
        self, auth_client, auth_user, member_shot, task_factory
    ):
        task = task_factory(project=member_shot.project, name="Замена неба")

        response = post_json(
            auth_client,
            f"/api/v1/shots/{member_shot.id}/tasks/",
            {"task_id": task.id},
        )

        assert response.status_code == HTTPStatus.CREATED, response.content
        (message,) = _system(member_shot)
        assert message.event == "task_added"
        assert message.created_by == auth_user
        assert message.payload == {
            "shot_task_id": response.json()["id"],
            "task_id": task.id,
            "task_code": task.code,
            "task_name": "Замена неба",
            "status": {
                "id": response.json()["status_id"],
                "name": "Не начата",
            },
        }

    def test_a_rejected_placement_records_nothing(
        self, auth_client, member_shot, task_factory, shot_task_factory
    ):
        task = task_factory(project=member_shot.project)
        shot_task_factory(shot=member_shot, task=task)

        response = post_json(
            auth_client,
            f"/api/v1/shots/{member_shot.id}/tasks/",
            {"task_id": task.id},
        )

        assert response.status_code == HTTPStatus.CONFLICT
        assert _system(member_shot) == []


class TestStatusAndAssigneeChanged:
    @pytest.fixture
    def member_shot_task(self, auth_user, shot_task, project_membership_factory):
        project_membership_factory(user=auth_user, project=shot_task.shot.project)
        return shot_task

    def _url(self, shot_task):
        return f"/api/v1/shot-tasks/{shot_task.id}/"

    def test_a_status_change_records_the_old_and_the_new_status(
        self, auth_client, auth_user, member_shot_task
    ):
        old = member_shot_task.status
        done = _status(member_shot_task.shot.project, "Готова")

        response = patch_json(
            auth_client, self._url(member_shot_task), {"status_id": done.id}
        )

        assert response.status_code == HTTPStatus.OK, response.content
        (message,) = _system(member_shot_task.shot)
        assert message.event == "status_changed"
        assert message.created_by == auth_user
        assert message.payload["from"] == {"id": old.id, "name": old.name}
        assert message.payload["to"] == {"id": done.id, "name": "Готова"}
        assert message.payload["task_code"] == member_shot_task.task.code

    def test_the_same_status_records_nothing(self, auth_client, member_shot_task):
        response = patch_json(
            auth_client,
            self._url(member_shot_task),
            {"status_id": member_shot_task.status_id},
        )

        assert response.status_code == HTTPStatus.OK
        assert _system(member_shot_task.shot) == []

    def test_assigning_records_who_was_assigned(
        self, auth_client, auth_user, member_shot_task
    ):
        response = patch_json(
            auth_client,
            self._url(member_shot_task),
            {"assignee_id": auth_user.id},
        )

        assert response.status_code == HTTPStatus.OK, response.content
        (message,) = _system(member_shot_task.shot)
        assert message.event == "assignee_changed"
        assert message.payload["from"] is None
        assert message.payload["to"] == {
            "id": auth_user.id,
            "name": auth_user.get_full_name(),
        }

    def test_reassigning_and_unassigning(
        self, auth_client, auth_user, member_shot_task, project_membership_factory
    ):
        other = project_membership_factory(project=member_shot_task.shot.project).user
        member_shot_task.assignee = auth_user
        member_shot_task.save()

        patch_json(auth_client, self._url(member_shot_task), {"assignee_id": other.id})
        patch_json(auth_client, self._url(member_shot_task), {"assignee_id": None})

        first, second = _system(member_shot_task.shot)
        assert first.payload["from"]["id"] == auth_user.id
        assert first.payload["to"]["id"] == other.id
        assert second.payload["from"]["id"] == other.id
        assert second.payload["to"] is None

    def test_the_same_assignee_records_nothing(
        self, auth_client, auth_user, member_shot_task
    ):
        member_shot_task.assignee = auth_user
        member_shot_task.save()

        patch_json(
            auth_client,
            self._url(member_shot_task),
            {"assignee_id": auth_user.id},
        )

        assert _system(member_shot_task.shot) == []

    def test_changing_both_records_two_events(
        self, auth_client, auth_user, member_shot_task
    ):
        done = _status(member_shot_task.shot.project, "Готова")

        patch_json(
            auth_client,
            self._url(member_shot_task),
            {"status_id": done.id, "assignee_id": auth_user.id},
        )

        events = [m.event for m in _system(member_shot_task.shot)]
        assert events == ["status_changed", "assignee_changed"]

    def test_changing_only_hours_records_nothing(self, auth_client, member_shot_task):
        response = patch_json(
            auth_client, self._url(member_shot_task), {"estimated_hours": "4"}
        )

        assert response.status_code == HTTPStatus.OK
        assert _system(member_shot_task.shot) == []

    def test_a_rejected_change_records_nothing(
        self, auth_client, member_shot_task, user_factory
    ):
        outsider = user_factory()  # not a project member

        response = patch_json(
            auth_client, self._url(member_shot_task), {"assignee_id": outsider.id}
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert _system(member_shot_task.shot) == []
