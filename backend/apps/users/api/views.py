from http import HTTPStatus

from django.core.paginator import Paginator
from django.db.models import Q
from dmr import APIError, Body, Controller, Path, Query, ResponseSpec, modify
from dmr.errors import ErrorType
from dmr.plugins.pydantic import PydanticFastSerializer
from dmr.security import AuthenticatedHttpRequest

from apps.auth.api.views import access_token_auth
from apps.users.models import User

from .schemas import (
    UserCreateIn,
    UserListOut,
    UserListQuery,
    UserOut,
    UserPath,
    UserUpdateIn,
)


def _serialize_user(request, user: User) -> UserOut:
    avatar_url = request.build_absolute_uri(user.avatar.url) if user.avatar else None
    return UserOut(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        avatar=avatar_url,
        is_active=user.is_active,
        date_joined=user.date_joined,
    )


def _get_user_or_404(user_id: int) -> User:
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist as exc:
        raise APIError(
            {"detail": f"User with id={user_id} was not found."},
            status_code=HTTPStatus.NOT_FOUND,
        ) from exc


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
        return _serialize_user(self.request, self.request.user)


class UserListController(Controller[PydanticFastSerializer]):
    """`GET/POST /api/v1/users/` - list and create users.

    Any authenticated user may list or create users; finer-grained
    permissions are deferred until they're actually needed.
    """

    request: AuthenticatedHttpRequest[User]
    auth = (access_token_auth,)

    @modify(
        summary="List users",
        description=(
            "Return a paginated list of users, optionally filtered by "
            "`search` against email, first and last name."
        ),
        response_description="A page of users.",
        tags=["Users"],
    )
    def get(self, parsed_query: Query[UserListQuery]) -> UserListOut:
        queryset = User.objects.all()

        if parsed_query.search:
            queryset = queryset.filter(
                Q(email__icontains=parsed_query.search)
                | Q(first_name__icontains=parsed_query.search)
                | Q(last_name__icontains=parsed_query.search),
            )

        paginator = Paginator(queryset, parsed_query.page_size)
        page = paginator.get_page(parsed_query.page)

        return UserListOut(
            items=[_serialize_user(self.request, user) for user in page.object_list],
            total=paginator.count,
            page=parsed_query.page,
            page_size=parsed_query.page_size,
        )

    @modify(
        status_code=HTTPStatus.CREATED,
        summary="Create a user",
        description=(
            "Create a new user account. If `password` is omitted, the "
            "account is created with an unusable password."
        ),
        response_description="The created user.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.BAD_REQUEST),
        ],
        tags=["Users"],
    )
    def post(self, parsed_body: Body[UserCreateIn]) -> UserOut:
        if User.objects.filter(email__iexact=parsed_body.email).exists():
            raise APIError(
                self.format_error(
                    "A user with this email already exists.",
                    loc=["email"],
                    error_type=ErrorType.value_error,
                ),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        user = User.objects.create_user(
            email=parsed_body.email,
            password=parsed_body.password,
            first_name=parsed_body.first_name,
            last_name=parsed_body.last_name,
        )
        return _serialize_user(self.request, user)


class UserDetailController(Controller[PydanticFastSerializer]):
    """`GET/PATCH/DELETE /api/v1/users/<id>/` - manage a single user."""

    request: AuthenticatedHttpRequest[User]
    auth = (access_token_auth,)

    @modify(
        summary="Get a user",
        description="Return a single user by id.",
        response_description="The requested user.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
        ],
        tags=["Users"],
    )
    def get(self, parsed_path: Path[UserPath]) -> UserOut:
        user = _get_user_or_404(parsed_path.user_id)
        return _serialize_user(self.request, user)

    @modify(
        summary="Update a user",
        description="Partially update a user. Only provided fields are changed.",
        response_description="The updated user.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
        ],
        tags=["Users"],
    )
    def patch(
        self,
        parsed_path: Path[UserPath],
        parsed_body: Body[UserUpdateIn],
    ) -> UserOut:
        user = _get_user_or_404(parsed_path.user_id)

        update_fields = parsed_body.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(user, field, value)
        if update_fields:
            user.save(update_fields=list(update_fields))

        return _serialize_user(self.request, user)

    @modify(
        status_code=HTTPStatus.NO_CONTENT,
        summary="Delete a user",
        description="Permanently delete a user account.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
        ],
        tags=["Users"],
    )
    def delete(self, parsed_path: Path[UserPath]) -> None:
        user = _get_user_or_404(parsed_path.user_id)
        user.delete()
        return None
