import pydantic


class LoginPayload(pydantic.BaseModel):
    """Credentials used to obtain a new access/refresh token pair."""

    email: str = pydantic.Field(
        description="Registered user's email address.",
        examples=["user@example.com"],
    )
    password: str = pydantic.Field(
        description="User's password.",
        examples=["W5&faQ36$f6"],
    )


class RefreshPayload(pydantic.BaseModel):
    """A refresh token used to obtain a new token pair without re-authenticating."""

    refresh_token: str = pydantic.Field(
        description="A valid, non-expired, non-revoked refresh token.",
    )


class LogoutPayload(pydantic.BaseModel):
    """Optional payload for logging out.

    If a refresh token is provided, it is blocklisted together with the
    access token used to authenticate this request, so it can no longer
    be used to mint new token pairs either.
    """

    refresh_token: str | None = pydantic.Field(
        default=None,
        description=(
            "Refresh token issued alongside the access token used for "
            "this request. If provided, it is revoked too, fully "
            "closing this session."
        ),
    )


class TokenPairResponse(pydantic.BaseModel):
    """A freshly issued pair of JWT tokens."""

    access_token: str = pydantic.Field(
        description="Short-lived JWT. Send it as `Authorization: Bearer "
        "<access_token>` on protected endpoints.",
    )
    refresh_token: str = pydantic.Field(
        description="Long-lived JWT. Exchange it for a new token pair "
        "at `POST /api/v1/auth/refresh/`.",
    )


class MessageResponse(pydantic.BaseModel):
    """A simple textual confirmation message."""

    detail: str = pydantic.Field(description="Human-readable result message.")


class UserOut(pydantic.BaseModel):
    """Public representation of the currently authenticated user."""

    id: int = pydantic.Field(description="Internal numeric user identifier.")
    email: str = pydantic.Field(description="User's email address.")
    first_name: str = pydantic.Field(description="User's first name.")
    last_name: str = pydantic.Field(description="User's last name.")
