import datetime as dt
from http import HTTPStatus
from typing import override

from django.conf import settings
from dmr import Body, Controller, modify
from dmr.exceptions import NotAuthenticatedError
from dmr.plugins.pydantic import PydanticFastSerializer
from dmr.security import AuthenticatedHttpRequest
from dmr.security.jwt import JWToken, JWTSyncAuth, request_jwt
from dmr.security.jwt.blocklist import JWTokenBlocklistSyncMixin
from dmr.security.jwt.views import (
    ObtainTokensPayload,
    ObtainTokensSyncController,
    RefreshTokenSyncController,
)

from apps.users.models import User

from .schemas import (
    LoginPayload,
    LogoutPayload,
    MessageResponse,
    RefreshPayload,
    TokenPairResponse,
    UserOut,
)


class AccessTokenAuth(JWTSyncAuth):
    """JWT auth that only accepts access tokens.

    ``JWTSyncAuth`` on its own does not check the ``type`` claim we put
    into the token's ``extras``, so a refresh token would otherwise work
    just as well as an access token on any protected endpoint.
    """

    @override
    def check_auth(self, user, token: JWToken) -> None:
        super().check_auth(user, token)
        if token.extras.get("type") != "access":
            raise NotAuthenticatedError("Invalid token type.")


class AccessTokenBlocklistAuth(JWTokenBlocklistSyncMixin, AccessTokenAuth):
    """Access token auth that also honors the revoked-tokens blocklist."""


access_token_auth = AccessTokenBlocklistAuth()


def _make_token_pair(controller) -> TokenPairResponse:
    """Build an access/refresh token pair using the controller's jwt settings."""
    now = dt.datetime.now(dt.UTC)
    return TokenPairResponse(
        access_token=controller.create_jwt_token(
            expiration=now + controller.jwt_expiration,
            token_type="access",
        ),
        refresh_token=controller.create_jwt_token(
            expiration=now + controller.jwt_refresh_expiration,
            token_type="refresh",
        ),
    )


class LoginController(
    ObtainTokensSyncController[
        PydanticFastSerializer,
        LoginPayload,
        TokenPairResponse,
    ],
):
    """`POST /api/v1/auth/login/` - exchange email+password for a token pair."""

    @override
    def convert_auth_payload(self, payload: LoginPayload) -> ObtainTokensPayload:
        # `authenticate()` is called with these kwargs. Even though our
        # USERNAME_FIELD is "email", Django's ModelBackend still expects
        # the value under the "username" kwarg name.
        return {"username": payload.email, "password": payload.password}

    @override
    def make_api_response(self) -> TokenPairResponse:
        return _make_token_pair(self)

    @modify(
        status_code=HTTPStatus.OK,
        summary="Log in",
        description=(
            "Authenticate with an email and password and receive a new "
            "pair of JWT tokens.\n\n"
            "- The **access token** is short-lived and must be sent as "
            "`Authorization: Bearer <access_token>` on protected "
            "endpoints.\n"
            "- The **refresh token** is long-lived and can be exchanged "
            "for a new pair at `POST /api/v1/auth/refresh/`."
        ),
        response_description="A new access/refresh token pair.",
        tags=["Auth"],
    )
    @override
    def post(self, parsed_body: Body[LoginPayload]) -> TokenPairResponse:
        return super().post(parsed_body)


class RefreshController(
    RefreshTokenSyncController[
        PydanticFastSerializer,
        RefreshPayload,
        TokenPairResponse,
    ],
):
    """`POST /api/v1/auth/refresh/` - exchange a refresh token for a new pair."""

    @override
    def convert_refresh_payload(self, payload: RefreshPayload) -> str:
        return payload.refresh_token

    @override
    def make_api_response(self) -> TokenPairResponse:
        return _make_token_pair(self)

    @override
    def refresh(self, parsed_body: RefreshPayload) -> TokenPairResponse:
        # `RefreshTokenSyncController` does not check the blocklist for
        # refresh tokens by default, only `AccessTokenBlocklistAuth` does
        # that for access tokens. We decode the token ourselves first so a
        # revoked (e.g. logged-out) refresh token can't mint new tokens.
        token = JWToken.decode(
            self.convert_refresh_payload(parsed_body),
            secret=self.jwt_secret or settings.SECRET_KEY,
            algorithm=self.jwt_algorithm,
        )
        is_revoked = (
            access_token_auth.blocklist_model()
            .objects.filter(
                jti=token.jti,
            )
            .exists()
        )
        if is_revoked:
            raise NotAuthenticatedError("Token has been revoked.")
        return super().refresh(parsed_body)

    @modify(
        status_code=HTTPStatus.OK,
        summary="Refresh tokens",
        description=(
            "Exchange a valid, non-revoked refresh token for a brand "
            "new access/refresh token pair, without sending the user's "
            "password again."
        ),
        response_description="A new access/refresh token pair.",
        tags=["Auth"],
    )
    @override
    def post(self, parsed_body: Body[RefreshPayload]) -> TokenPairResponse:
        return super().post(parsed_body)


class LogoutController(Controller[PydanticFastSerializer]):
    """`POST /api/v1/auth/logout/` - revoke the current session's tokens."""

    request: AuthenticatedHttpRequest[User]
    auth = (access_token_auth,)

    @modify(
        status_code=HTTPStatus.OK,
        summary="Log out",
        description=(
            "Revoke the access token used to authenticate this request, "
            "so it can no longer be used, even if it has not expired "
            "yet.\n\n"
            "Optionally pass the paired **refresh token** in the body to "
            "revoke it too and fully close the session; otherwise it "
            "stays valid until it expires naturally."
        ),
        response_description="Confirmation that the session was closed.",
        tags=["Auth"],
    )
    def post(self, parsed_body: Body[LogoutPayload]) -> MessageResponse:
        access_token = request_jwt(self.request, strict=True)
        access_token_auth.blocklist(access_token)

        if parsed_body.refresh_token:
            try:
                refresh_token = JWToken.decode(
                    parsed_body.refresh_token,
                    secret=settings.SECRET_KEY,
                    algorithm="HS256",
                )
            except NotAuthenticatedError:
                pass  # Garbage or already-expired token: nothing to revoke.
            else:
                access_token_auth.blocklist(refresh_token)

        return MessageResponse(detail="Successfully logged out.")


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
