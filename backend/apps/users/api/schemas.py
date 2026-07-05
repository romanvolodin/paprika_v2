import pydantic


class UserOut(pydantic.BaseModel):
    """Public representation of the currently authenticated user."""

    id: int = pydantic.Field(description="Internal numeric user identifier.")
    email: str = pydantic.Field(description="User's email address.")
    first_name: str = pydantic.Field(description="User's first name.")
    last_name: str = pydantic.Field(description="User's last name.")
