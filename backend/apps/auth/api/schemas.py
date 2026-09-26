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
