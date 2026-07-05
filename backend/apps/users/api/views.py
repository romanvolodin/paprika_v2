from dmr import Controller, modify
from dmr.plugins.pydantic import PydanticFastSerializer
from dmr.security import AuthenticatedHttpRequest

from apps.auth.api.views import access_token_auth
from apps.users.models import User

from .schemas import UserOut


class MeController(Controller[PydanticFastSerializer]):
    """`GET /api/v1/users/me/` - return the currently authenticated user."""

    request: AuthenticatedHttpRequest[User]
    auth = (access_token_auth,)

    @modify(
        summary="Get current user",
        description="Return the profile of the user identified by the "
        "provided access token.",
        response_description="The currently authenticated user.",
        tags=["Users"],
    )
    def get(self) -> UserOut:
        user = self.request.user
        return UserOut(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )
