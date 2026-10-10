"""System chat messages: records of things that happened on a shot.

The API handlers that perform the actions call these inside their own
`transaction.atomic()` block, so the action and its chat message are saved
(or rolled back) together. They are plain function calls rather than
signals on purpose: a signal also fires for migrations, the admin and
tests, and doesn't know which user did the action.

The `payload` keeps ids *and* names as they were at the moment of the
event, so the line stays readable after the version, task or status is
renamed or deleted. The client builds the sentence from `event` and
`payload`.
"""

from apps.tasks.models import ShotTask, TaskStatus
from apps.users.models import User
from apps.versions.models import Version

from .models import Message


def _user_ref(user: User | None) -> dict | None:
    if user is None:
        return None
    return {"id": user.id, "name": user.get_full_name()}


def _status_ref(status: TaskStatus) -> dict:
    return {"id": status.id, "name": status.name}


def _shot_task_payload(shot_task: ShotTask) -> dict:
    task = shot_task.task
    return {
        "shot_task_id": shot_task.id,
        "task_id": task.id,
        "task_code": task.code,
        "task_name": task.name,
    }


def _record(shot, user: User, event: str, payload: dict) -> Message:
    return Message.objects.create(
        shot=shot,
        type=Message.Type.SYSTEM,
        event=event,
        payload=payload,
        created_by=user,
        updated_by=user,
    )


def record_version_uploaded(version: Version, user: User) -> Message:
    message = _record(
        version.shot,
        user,
        Message.Event.VERSION_UPLOADED,
        {"version_id": version.id, "version_name": version.name},
    )
    # So the version can be opened straight from the chat.
    message.versions.add(version)
    return message


def record_task_added(shot_task: ShotTask, user: User) -> Message:
    return _record(
        shot_task.shot,
        user,
        Message.Event.TASK_ADDED,
        {**_shot_task_payload(shot_task), "status": _status_ref(shot_task.status)},
    )


def record_status_changed(
    shot_task: ShotTask, old_status: TaskStatus, user: User
) -> Message:
    return _record(
        shot_task.shot,
        user,
        Message.Event.STATUS_CHANGED,
        {
            **_shot_task_payload(shot_task),
            "from": _status_ref(old_status),
            "to": _status_ref(shot_task.status),
        },
    )


def record_assignee_changed(
    shot_task: ShotTask, old_assignee: User | None, user: User
) -> Message:
    return _record(
        shot_task.shot,
        user,
        Message.Event.ASSIGNEE_CHANGED,
        {
            **_shot_task_payload(shot_task),
            "from": _user_ref(old_assignee),
            "to": _user_ref(shot_task.assignee),
        },
    )
