from http import HTTPStatus

from django.core.paginator import Paginator
from dmr import APIError, Body, Controller, Path, Query, ResponseSpec, modify
from dmr.errors import ErrorType
from dmr.plugins.pydantic import PydanticSerializer
from dmr.security import AuthenticatedHttpRequest

from apps.auth.api.views import access_token_auth
from apps.projects.api.views import _get_project_or_404
from apps.shots.models import ShotGroup
from apps.users.api.views import _serialize_user
from apps.users.models import User

from .schemas import (
    ProjectShotGroupsPath,
    ShotGroupCreateIn,
    ShotGroupListOut,
    ShotGroupListQuery,
    ShotGroupOut,
    ShotGroupPath,
    ShotGroupUpdateIn,
)


def _serialize_shot_group(request, shot_group: ShotGroup) -> ShotGroupOut:
    return ShotGroupOut(
        id=shot_group.id,
        project_id=shot_group.project_id,
        name=shot_group.name,
        created_by=_serialize_user(request, shot_group.created_by)
        if shot_group.created_by
        else None,
        updated_by=_serialize_user(request, shot_group.updated_by)
        if shot_group.updated_by
        else None,
        created_at=shot_group.created_at,
        updated_at=shot_group.updated_at,
    )


def _get_shot_group_or_404(user: User, shot_group_id: int) -> ShotGroup:
    """Look up a shot group, scoped to projects the user is a member of.

    Mirrors `apps.projects.api.views._get_project_or_404` - visibility
    follows the parent project's `ProjectMembership`; there's no separate
    membership model for shot groups.
    """
    try:
        return (
            ShotGroup.objects.filter(project__memberships__user=user)
            .distinct()
            .get(pk=shot_group_id)
        )
    except ShotGroup.DoesNotExist as exc:
        raise APIError(
            {"detail": f"Shot group with id={shot_group_id} was not found."},
            status_code=HTTPStatus.NOT_FOUND,
        ) from exc


class ShotGroupListController(Controller[PydanticSerializer]):
    """`GET/POST /api/v1/projects/<project_id>/shot-groups/` - list and
    create shot groups within a project.
    """

    request: AuthenticatedHttpRequest[User]
    auth = (access_token_auth,)

    @modify(
        summary="List a project's shot groups",
        description=(
            "Return a paginated list of shot groups within the given "
            "project, optionally filtered by `search` against the name."
        ),
        response_description="A page of shot groups.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
        ],
        tags=["Shot groups"],
    )
    def get(
        self,
        parsed_path: Path[ProjectShotGroupsPath],
        parsed_query: Query[ShotGroupListQuery],
    ) -> ShotGroupListOut:
        project = _get_project_or_404(self.request.user, parsed_path.project_id)

        queryset = ShotGroup.objects.filter(project=project)

        if parsed_query.search:
            queryset = queryset.filter(name__icontains=parsed_query.search)

        paginator = Paginator(queryset, parsed_query.page_size)
        page = paginator.get_page(parsed_query.page)

        return ShotGroupListOut(
            items=[
                _serialize_shot_group(self.request, shot_group)
                for shot_group in page.object_list
            ],
            total=paginator.count,
            page=parsed_query.page,
            page_size=parsed_query.page_size,
        )

    @modify(
        status_code=HTTPStatus.CREATED,
        summary="Create a shot group",
        description="Create a new shot group within the project.",
        response_description="The created shot group.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
            ResponseSpec(dict, status_code=HTTPStatus.BAD_REQUEST),
        ],
        tags=["Shot groups"],
    )
    def post(
        self,
        parsed_path: Path[ProjectShotGroupsPath],
        parsed_body: Body[ShotGroupCreateIn],
    ) -> ShotGroupOut:
        project = _get_project_or_404(self.request.user, parsed_path.project_id)

        if ShotGroup.objects.filter(project=project, name=parsed_body.name).exists():
            raise APIError(
                self.format_error(
                    "A shot group with this name already exists in this project.",
                    loc=["name"],
                    error_type=ErrorType.value_error,
                ),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        shot_group = ShotGroup.objects.create(
            project=project,
            name=parsed_body.name,
            created_by=self.request.user,
            updated_by=self.request.user,
        )
        return _serialize_shot_group(self.request, shot_group)


class ShotGroupDetailController(Controller[PydanticSerializer]):
    """`GET/PATCH/DELETE /api/v1/shot-groups/<id>/` - manage a single shot
    group.
    """

    request: AuthenticatedHttpRequest[User]
    auth = (access_token_auth,)

    @modify(
        summary="Get a shot group",
        description="Return a single shot group by id.",
        response_description="The requested shot group.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
        ],
        tags=["Shot groups"],
    )
    def get(self, parsed_path: Path[ShotGroupPath]) -> ShotGroupOut:
        shot_group = _get_shot_group_or_404(
            self.request.user, parsed_path.shot_group_id
        )
        return _serialize_shot_group(self.request, shot_group)

    @modify(
        summary="Rename a shot group",
        description="Update a shot group's name.",
        response_description="The updated shot group.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
            ResponseSpec(dict, status_code=HTTPStatus.BAD_REQUEST),
        ],
        tags=["Shot groups"],
    )
    def patch(
        self,
        parsed_path: Path[ShotGroupPath],
        parsed_body: Body[ShotGroupUpdateIn],
    ) -> ShotGroupOut:
        shot_group = _get_shot_group_or_404(
            self.request.user, parsed_path.shot_group_id
        )

        name_taken = (
            ShotGroup.objects.filter(project=shot_group.project, name=parsed_body.name)
            .exclude(pk=shot_group.pk)
            .exists()
        )
        if name_taken:
            raise APIError(
                self.format_error(
                    "A shot group with this name already exists in this project.",
                    loc=["name"],
                    error_type=ErrorType.value_error,
                ),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        shot_group.name = parsed_body.name
        shot_group.updated_by = self.request.user
        shot_group.save(update_fields=["name", "updated_by"])

        return _serialize_shot_group(self.request, shot_group)

    @modify(
        status_code=HTTPStatus.NO_CONTENT,
        summary="Delete a shot group",
        description="Permanently delete a shot group.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
        ],
        tags=["Shot groups"],
    )
    def delete(self, parsed_path: Path[ShotGroupPath]) -> None:
        shot_group = _get_shot_group_or_404(
            self.request.user, parsed_path.shot_group_id
        )
        shot_group.delete()
        return None
