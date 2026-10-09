import datetime as dt
from decimal import Decimal
from typing import Annotated

import pydantic

from apps.users.api.schemas import UserOut


_COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}$"
_ABBREVIATION_PATTERN = r"^[A-Z0-9]{2,5}$"

Hours = Annotated[
    Decimal,
    pydantic.Field(ge=0, max_digits=6, decimal_places=2),
]


# --- task types -------------------------------------------------------------


class TaskTypeOut(pydantic.BaseModel):
    """Public representation of a task type."""

    id: int
    company_id: int
    name: str
    abbreviation: str = pydantic.Field(
        description="Prefix of the codes of tasks of this type, e.g. `CLN`."
    )
    color: str = pydantic.Field(description="Hex color, e.g. `#FF5733`.")
    created_by: UserOut | None = pydantic.Field(
        description="The user who created the type, or null if that user "
        "has since been deleted."
    )
    updated_by: UserOut | None = pydantic.Field(
        description="The user who last updated the type, or null if that "
        "user has since been deleted."
    )
    created_at: dt.datetime
    updated_at: dt.datetime


class TaskTypeListQuery(pydantic.BaseModel):
    """Query params for `GET /api/v1/companies/<id>/task-types/`.

    No pagination - a company's task types are a short, bounded list.
    """

    search: str | None = pydantic.Field(
        default=None,
        description="Case-insensitive match against the name or abbreviation.",
    )


class TaskTypeListOut(pydantic.BaseModel):
    """The full list of a company's task types (not paginated)."""

    items: list[TaskTypeOut]


class CompanyTaskTypesPath(pydantic.BaseModel):
    """URL path parameters identifying a company's task types collection."""

    company_id: int = pydantic.Field(gt=0)


class TaskTypePath(pydantic.BaseModel):
    """URL path parameters identifying a single task type."""

    task_type_id: int = pydantic.Field(gt=0)


class TaskTypeCreateIn(pydantic.BaseModel):
    """Payload for `POST /api/v1/companies/<company_id>/task-types/`."""

    name: str = pydantic.Field(min_length=1, max_length=255)
    abbreviation: str = pydantic.Field(
        pattern=_ABBREVIATION_PATTERN,
        description="2-5 uppercase Latin letters or digits. Unique within the company.",
    )
    color: str = pydantic.Field(pattern=_COLOR_PATTERN)


class TaskTypeUpdateIn(pydantic.BaseModel):
    """Payload for `PATCH /api/v1/task-types/<id>/`. All fields optional.

    Changing `abbreviation` doesn't touch the codes of existing tasks.
    """

    name: str | None = pydantic.Field(default=None, min_length=1, max_length=255)
    abbreviation: str | None = pydantic.Field(
        default=None, pattern=_ABBREVIATION_PATTERN
    )
    color: str | None = pydantic.Field(default=None, pattern=_COLOR_PATTERN)


# --- task statuses ----------------------------------------------------------


class TaskStatusOut(pydantic.BaseModel):
    """Public representation of a task status."""

    id: int
    company_id: int
    name: str
    color: str = pydantic.Field(description="Hex color, e.g. `#FF5733`.")
    order: int | None = pydantic.Field(
        description="Sort position among the primary workflow statuses; "
        "null for side states (e.g. cancelled, on hold)."
    )
    is_default: bool = pydantic.Field(
        description="Whether new shot tasks get this status when none is specified."
    )
    created_by: UserOut | None = pydantic.Field(
        description="The user who created the status, or null if that user "
        "has since been deleted."
    )
    updated_by: UserOut | None = pydantic.Field(
        description="The user who last updated the status, or null if that "
        "user has since been deleted."
    )
    created_at: dt.datetime
    updated_at: dt.datetime


class TaskStatusListQuery(pydantic.BaseModel):
    """Query params for `GET /api/v1/companies/<id>/task-statuses/`.

    No pagination - a company's task statuses are a short, bounded list.
    """

    search: str | None = pydantic.Field(
        default=None,
        description="Case-insensitive match against the status name.",
    )


class TaskStatusListOut(pydantic.BaseModel):
    """The full list of a company's task statuses (not paginated)."""

    items: list[TaskStatusOut]


class CompanyTaskStatusesPath(pydantic.BaseModel):
    """URL path parameters identifying a company's task statuses collection."""

    company_id: int = pydantic.Field(gt=0)


class TaskStatusPath(pydantic.BaseModel):
    """URL path parameters identifying a single task status."""

    task_status_id: int = pydantic.Field(gt=0)


class TaskStatusCreateIn(pydantic.BaseModel):
    """Payload for `POST /api/v1/companies/<company_id>/task-statuses/`.

    `order` left unset means this status is a side state, not part of
    the primary ordered workflow. Setting `is_default=True`
    automatically unsets the company's previous default.
    """

    name: str = pydantic.Field(min_length=1, max_length=255)
    color: str = pydantic.Field(pattern=_COLOR_PATTERN)
    order: int | None = None
    is_default: bool = False


class TaskStatusUpdateIn(pydantic.BaseModel):
    """Payload for `PATCH /api/v1/task-statuses/<id>/`. All fields optional."""

    name: str | None = pydantic.Field(default=None, min_length=1, max_length=255)
    color: str | None = pydantic.Field(default=None, pattern=_COLOR_PATTERN)
    order: int | None = None
    is_default: bool | None = None


# --- tasks ------------------------------------------------------------------


class TaskOut(pydantic.BaseModel):
    """Public representation of a task."""

    id: int
    project_id: int
    code: str = pydantic.Field(
        description="Public identifier: the type's abbreviation plus four "
        "digits, e.g. `CLN4821`. Unique within the project and never changes."
    )
    name: str
    description: str
    type_id: int = pydantic.Field(description="Id of the task's type.")
    shot_ids: list[int] = pydantic.Field(
        description="Ids of the shots the task is placed on. Empty for a "
        "standalone task."
    )
    created_by: UserOut | None = pydantic.Field(
        description="The user who created the task, or null if that user "
        "has since been deleted."
    )
    updated_by: UserOut | None = pydantic.Field(
        description="The user who last updated the task, or null if that "
        "user has since been deleted."
    )
    created_at: dt.datetime
    updated_at: dt.datetime


class TaskListQuery(pydantic.BaseModel):
    """Pagination and filter params for `GET /api/v1/projects/<id>/tasks/`."""

    page: int = pydantic.Field(default=1, ge=1, description="1-indexed page number.")
    page_size: int = pydantic.Field(
        default=20,
        ge=1,
        le=100,
        description="Number of tasks per page.",
    )
    search: str | None = pydantic.Field(
        default=None,
        description="Case-insensitive match against the task name or code.",
    )
    type: int | None = pydantic.Field(
        default=None, description="Only tasks of the task type with this id."
    )


class TaskListOut(pydantic.BaseModel):
    """A page of tasks, newest first."""

    items: list[TaskOut]
    total: int = pydantic.Field(description="Total number of tasks matching filters.")
    page: int
    page_size: int


class ProjectTasksPath(pydantic.BaseModel):
    """URL path parameters identifying a project's tasks collection."""

    project_id: int = pydantic.Field(gt=0)


class TaskPath(pydantic.BaseModel):
    """URL path parameters identifying a single task."""

    task_id: int = pydantic.Field(gt=0)


class TaskCreateIn(pydantic.BaseModel):
    """Payload for `POST /api/v1/projects/<project_id>/tasks/`.

    The task starts out standalone; place it on shots with
    `POST /api/v1/shots/<id>/tasks/`.
    """

    name: str = pydantic.Field(min_length=1, max_length=255)
    description: str = ""
    type_id: int = pydantic.Field(
        description="Id of a task type of the project's company."
    )


class TaskUpdateIn(pydantic.BaseModel):
    """Payload for `PATCH /api/v1/tasks/<id>/`. All fields optional.

    Changing `type_id` doesn't change the task's `code`.
    """

    name: str | None = pydantic.Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    type_id: int | None = pydantic.Field(
        default=None,
        description=(
            "Id of a task type of the project's company. Since `type` "
            "can't be null on a task, sending this as null is rejected - "
            "omit the field entirely to leave the type unchanged."
        ),
    )


# --- shot tasks -------------------------------------------------------------


class ShotTaskOut(pydantic.BaseModel):
    """A task placed on a shot, with the tracking of the work done there."""

    id: int
    shot_id: int
    task: TaskOut
    status_id: int = pydantic.Field(
        description="Id of the task's current status on this shot."
    )
    assignee: UserOut | None = pydantic.Field(
        description="Who is doing the task on this shot, or null."
    )
    estimated_hours: float | None = pydantic.Field(
        description="Estimated time in hours, or null if not set."
    )
    actual_hours: float | None = pydantic.Field(
        description="Time actually spent in hours, or null if not set."
    )
    created_by: UserOut | None = pydantic.Field(
        description="The user who placed the task on the shot, or null if "
        "that user has since been deleted."
    )
    updated_by: UserOut | None = pydantic.Field(
        description="The user who last updated this record, or null if "
        "that user has since been deleted."
    )
    created_at: dt.datetime
    updated_at: dt.datetime


class ShotTaskListOut(pydantic.BaseModel):
    """Every task placed on a shot, in creation order (not paginated)."""

    items: list[ShotTaskOut]


class ShotTasksPath(pydantic.BaseModel):
    """URL path parameters identifying a shot's tasks collection."""

    shot_id: int = pydantic.Field(gt=0)


class ShotTaskPath(pydantic.BaseModel):
    """URL path parameters identifying a single shot task."""

    shot_task_id: int = pydantic.Field(gt=0)


class ShotTaskCreateIn(pydantic.BaseModel):
    """Payload for `POST /api/v1/shots/<shot_id>/tasks/`."""

    task_id: int = pydantic.Field(
        description="Id of an existing task of the same project as the shot."
    )
    status_id: int | None = pydantic.Field(
        default=None,
        description="Id of a status of the project's company. Defaults to "
        "the company's default task status.",
    )
    assignee_id: int | None = pydantic.Field(
        default=None,
        description="Id of a member of the project, or null for nobody.",
    )
    estimated_hours: Hours | None = None
    actual_hours: Hours | None = None


class ShotTaskUpdateIn(pydantic.BaseModel):
    """Payload for `PATCH /api/v1/shot-tasks/<id>/`. All fields optional.

    The task and the shot can't be changed; delete the shot task and
    create a new one instead.
    """

    status_id: int | None = pydantic.Field(
        default=None,
        description=(
            "Id of a status of the project's company. Since `status` "
            "can't be null, sending this as null is rejected - omit the "
            "field entirely to leave the status unchanged."
        ),
    )
    assignee_id: int | None = pydantic.Field(
        default=None,
        description="Id of a member of the project, or null to unassign.",
    )
    estimated_hours: Hours | None = None
    actual_hours: Hours | None = None
