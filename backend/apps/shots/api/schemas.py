import datetime as dt

import pydantic

from apps.users.api.schemas import UserOut


class ShotGroupOut(pydantic.BaseModel):
    """Public representation of a shot group."""

    id: int = pydantic.Field(description="Internal numeric shot group identifier.")
    project_id: int
    name: str = pydantic.Field(description="Shot group name.")
    created_by: UserOut | None = pydantic.Field(
        description="The user who created the shot group, or null if that "
        "user has since been deleted."
    )
    updated_by: UserOut | None = pydantic.Field(
        description="The user who last updated the shot group, or null if "
        "that user has since been deleted."
    )
    created_at: dt.datetime
    updated_at: dt.datetime


class ShotGroupListQuery(pydantic.BaseModel):
    """Pagination and search params for `GET /api/v1/projects/<id>/shot-groups/`."""

    page: int = pydantic.Field(default=1, ge=1, description="1-indexed page number.")
    page_size: int = pydantic.Field(
        default=20,
        ge=1,
        le=100,
        description="Number of shot groups per page.",
    )
    search: str | None = pydantic.Field(
        default=None,
        description="Case-insensitive match against the shot group name.",
    )


class ShotGroupListOut(pydantic.BaseModel):
    """A page of shot groups within a project."""

    items: list[ShotGroupOut]
    total: int = pydantic.Field(
        description="Total number of shot groups matching filters."
    )
    page: int
    page_size: int


class ProjectShotGroupsPath(pydantic.BaseModel):
    """URL path parameters identifying a project's shot groups collection."""

    project_id: int = pydantic.Field(gt=0)


class ShotGroupPath(pydantic.BaseModel):
    """URL path parameters identifying a single shot group."""

    shot_group_id: int = pydantic.Field(gt=0)


class ShotGroupCreateIn(pydantic.BaseModel):
    """Payload for `POST /api/v1/projects/<project_id>/shot-groups/`."""

    name: str = pydantic.Field(min_length=1, max_length=255)


class ShotGroupUpdateIn(pydantic.BaseModel):
    """Payload for `PATCH /api/v1/shot-groups/<id>/`.

    `name` is the only field there is, so unlike `ProjectUpdateIn` this
    isn't a partial-update schema - it's always required.
    """

    name: str = pydantic.Field(min_length=1, max_length=255)
