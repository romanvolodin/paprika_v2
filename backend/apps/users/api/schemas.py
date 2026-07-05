import datetime as dt

import pydantic


class UserOut(pydantic.BaseModel):
    """Public representation of a user."""

    id: int = pydantic.Field(description="Internal numeric user identifier.")
    email: str = pydantic.Field(description="User's email address.")
    first_name: str = pydantic.Field(description="User's first name.")
    last_name: str = pydantic.Field(description="User's last name.")
    avatar: str | None = pydantic.Field(
        default=None,
        description="Absolute URL of the user's avatar image, or null if none.",
    )
    is_active: bool = pydantic.Field(
        description="Whether the user account is active.",
    )
    date_joined: dt.datetime = pydantic.Field(
        description="When the user account was created.",
    )


class UserListQuery(pydantic.BaseModel):
    """Pagination and search params for `GET /api/v1/users/`."""

    page: int = pydantic.Field(default=1, ge=1, description="1-indexed page number.")
    page_size: int = pydantic.Field(
        default=20,
        ge=1,
        le=100,
        description="Number of users per page.",
    )
    search: str | None = pydantic.Field(
        default=None,
        description="Case-insensitive match against email, first or last name.",
    )


class UserListOut(pydantic.BaseModel):
    """A page of users."""

    items: list[UserOut]
    total: int = pydantic.Field(description="Total number of users matching filters.")
    page: int
    page_size: int


class UserPath(pydantic.BaseModel):
    """URL path parameters identifying a single user."""

    user_id: int = pydantic.Field(gt=0)


class UserCreateIn(pydantic.BaseModel):
    """Payload for `POST /api/v1/users/`."""

    email: pydantic.EmailStr
    password: str | None = pydantic.Field(
        default=None,
        min_length=8,
        description=(
            "If omitted, the account is created with an unusable password "
            "(e.g. for an invite-based flow)."
        ),
    )
    first_name: str = pydantic.Field(min_length=1, max_length=150)
    last_name: str = pydantic.Field(min_length=1, max_length=150)


class UserUpdateIn(pydantic.BaseModel):
    """Payload for `PATCH /api/v1/users/<id>/`. All fields are optional."""

    first_name: str | None = pydantic.Field(default=None, min_length=1, max_length=150)
    last_name: str | None = pydantic.Field(default=None, min_length=1, max_length=150)
    is_active: bool | None = None
