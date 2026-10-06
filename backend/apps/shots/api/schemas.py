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


class ShotOut(pydantic.BaseModel):
    """Public representation of a shot."""

    id: int = pydantic.Field(description="Internal numeric shot identifier.")
    project_id: int
    group_ids: list[int] = pydantic.Field(
        description="Ids of the shot groups this shot belongs to. May be empty."
    )
    name: str = pydantic.Field(description="Shot name. Immutable once set.")
    rec_timecode: int | None = pydantic.Field(
        description="Start position of the shot in the edit, in frames."
    )
    duration: int | None = pydantic.Field(description="Length of the shot, in frames.")
    created_by: UserOut | None = pydantic.Field(
        description="The user who created the shot, or null if that user "
        "has since been deleted."
    )
    updated_by: UserOut | None = pydantic.Field(
        description="The user who last updated the shot, or null if that "
        "user has since been deleted."
    )
    created_at: dt.datetime
    updated_at: dt.datetime


class ShotListQuery(pydantic.BaseModel):
    """Pagination and search params shared by both shot list endpoints
    (project- and group-scoped).
    """

    page: int = pydantic.Field(default=1, ge=1, description="1-indexed page number.")
    page_size: int = pydantic.Field(
        default=20,
        ge=1,
        le=100,
        description="Number of shots per page.",
    )
    search: str | None = pydantic.Field(
        default=None,
        description="Case-insensitive match against the shot name.",
    )


class ShotListOut(pydantic.BaseModel):
    """A page of shots."""

    items: list[ShotOut]
    total: int = pydantic.Field(description="Total number of shots matching filters.")
    page: int
    page_size: int


class ProjectShotsPath(pydantic.BaseModel):
    """URL path parameters identifying a project's shots collection."""

    project_id: int = pydantic.Field(gt=0)


class ShotGroupShotsPath(pydantic.BaseModel):
    """URL path parameters identifying a shot group's shots collection."""

    shot_group_id: int = pydantic.Field(gt=0)


class ShotPath(pydantic.BaseModel):
    """URL path parameters identifying a single shot."""

    shot_id: int = pydantic.Field(gt=0)


class ShotCreateIn(pydantic.BaseModel):
    """Payload for `POST /api/v1/projects/<project_id>/shots/`.

    This is the only place a shot is created - there's no corresponding
    create on the shot-group-scoped collection, to avoid two routes with
    subtly different creation semantics.
    """

    name: str = pydantic.Field(min_length=1, max_length=255)
    group_ids: list[int] = pydantic.Field(
        default_factory=list,
        description=(
            "Ids of shot groups (within the same project) to add this shot "
            "to. Optional - a shot may belong to none; there is no default "
            "or fallback group."
        ),
    )
    rec_timecode: int | None = pydantic.Field(
        default=None,
        ge=0,
        description="Start position of the shot in the edit, in frames.",
    )
    duration: int | None = pydantic.Field(
        default=None,
        ge=1,
        description="Length of the shot, in frames.",
    )


class ShotUpdateIn(pydantic.BaseModel):
    """Payload for `PATCH /api/v1/shots/<id>/`. All fields are optional.

    `name` is intentionally absent - like `Project.code`, it's immutable
    once the shot is created. `group_ids`, when present, *replaces* the
    full set of group memberships (it's not a merge/add) - send the
    complete desired list.
    """

    group_ids: list[int] | None = None
    rec_timecode: int | None = pydantic.Field(default=None, ge=0)
    duration: int | None = pydantic.Field(default=None, ge=1)
