import datetime as dt

import pydantic

from apps.users.api.schemas import UserOut
from apps.versions.media import ALLOWED_EXTENSIONS


_EXTENSION_PATTERN = r"(?i)^.+\.({})$".format("|".join(ALLOWED_EXTENSIONS))


class VersionFileMetadata(pydantic.BaseModel):
    """Validates the uploaded file's metadata before it is processed.

    Only the extension is checked here. The size limit is configurable
    (`PAPRIKA_VERSION_MAX_FILE_SIZE_MB`) and is enforced in the view so it
    can answer 413 instead of a validation error, and the file's actual
    contents are checked once it's been read.
    """

    name: str = pydantic.Field(
        max_length=255,
        pattern=_EXTENSION_PATTERN,
        description=f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}.",
    )
    size: int


class VersionFiles(pydantic.BaseModel):
    """Files accepted by `POST /api/v1/shots/<shot_id>/versions/`."""

    source: VersionFileMetadata


class VersionOut(pydantic.BaseModel):
    """Public representation of a version."""

    id: int
    project_id: int
    shot_id: int
    name: str = pydantic.Field(
        description="Taken from the uploaded file's name without its "
        "extension. Unique within the project; can't be changed."
    )
    type: str = pydantic.Field(description="`video` or `image`.")
    source: str = pydantic.Field(description="Absolute URL of the original file.")
    converted: str | None = pydantic.Field(
        description="Absolute URL of the browser-friendly rendition, or null "
        "if there is none yet. Clients should use it when present and fall "
        "back to `source`."
    )
    thumb: str | None = pydantic.Field(
        description="Absolute URL of a small JPG thumbnail, or null."
    )
    width: int = pydantic.Field(description="In pixels.")
    height: int = pydantic.Field(description="In pixels.")
    duration: int | None = pydantic.Field(
        description="Length in frames. Null for images."
    )
    fps: float | None = pydantic.Field(
        description="Frames per second. Null for images."
    )
    codec: str = pydantic.Field(
        description="Video codec name (e.g. `h264`). Empty for images."
    )
    file_size: int = pydantic.Field(description="Size of the source file, in bytes.")
    created_by: UserOut | None = pydantic.Field(
        description="The user who uploaded the version, or null if that "
        "user has since been deleted."
    )
    updated_by: UserOut | None
    created_at: dt.datetime
    updated_at: dt.datetime


class VersionListQuery(pydantic.BaseModel):
    """Pagination and search params for `GET /api/v1/shots/<id>/versions/`."""

    page: int = pydantic.Field(default=1, ge=1, description="1-indexed page number.")
    page_size: int = pydantic.Field(
        default=20,
        ge=1,
        le=100,
        description="Number of versions per page.",
    )
    search: str | None = pydantic.Field(
        default=None,
        description="Case-insensitive match against the version name.",
    )


class VersionListOut(pydantic.BaseModel):
    """A page of versions, newest first."""

    items: list[VersionOut]
    total: int = pydantic.Field(description="Total number of versions of the shot.")
    page: int
    page_size: int


class ShotVersionsPath(pydantic.BaseModel):
    """URL path parameters identifying a shot's versions collection."""

    shot_id: int = pydantic.Field(gt=0)


class VersionPath(pydantic.BaseModel):
    """URL path parameters identifying a single version."""

    version_id: int = pydantic.Field(gt=0)
