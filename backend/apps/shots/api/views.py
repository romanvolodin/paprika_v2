from http import HTTPStatus

from django.core.paginator import Paginator
from dmr import APIError, Body, Controller, Path, Query, ResponseSpec, modify
from dmr.errors import ErrorType
from dmr.plugins.pydantic import PydanticSerializer
from dmr.security import AuthenticatedHttpRequest

from apps.auth.api.views import access_token_auth
from apps.projects.api.views import _get_project_or_404
from apps.projects.models import Project
from apps.shots.models import Shot, ShotGroup
from apps.users.api.views import _serialize_user
from apps.users.models import User

from .schemas import (
    ProjectShotGroupsPath,
    ProjectShotsPath,
    ShotCreateIn,
    ShotGroupCreateIn,
    ShotGroupListOut,
    ShotGroupListQuery,
    ShotGroupOut,
    ShotGroupPath,
    ShotGroupShotsPath,
    ShotGroupUpdateIn,
    ShotListOut,
    ShotListQuery,
    ShotOut,
    ShotPath,
    ShotUpdateIn,
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


def _serialize_shot(request, shot: Shot) -> ShotOut:
    return ShotOut(
        id=shot.id,
        project_id=shot.project_id,
        group_ids=[group.id for group in shot.groups.all()],
        name=shot.name,
        rec_timecode=shot.rec_timecode,
        duration=shot.duration,
        created_by=_serialize_user(request, shot.created_by)
        if shot.created_by
        else None,
        updated_by=_serialize_user(request, shot.updated_by)
        if shot.updated_by
        else None,
        created_at=shot.created_at,
        updated_at=shot.updated_at,
    )


def _get_shot_or_404(user: User, shot_id: int) -> Shot:
    """Look up a shot, scoped to projects the user is a member of.

    Mirrors `_get_shot_group_or_404` - visibility follows the parent
    project's `ProjectMembership` directly, regardless of which (if any)
    groups the shot belongs to.
    """
    try:
        return (
            Shot.objects.filter(project__memberships__user=user)
            .distinct()
            .get(pk=shot_id)
        )
    except Shot.DoesNotExist as exc:
        raise APIError(
            {"detail": f"Shot with id={shot_id} was not found."},
            status_code=HTTPStatus.NOT_FOUND,
        ) from exc


def _resolve_group_ids(
    controller, project: Project, group_ids: list[int]
) -> list[ShotGroup]:
    """Resolve `group_ids` to `ShotGroup` rows, all belonging to `project`.

    Raises a 400 naming the first offending id if any group doesn't
    exist or belongs to a different project - groups aren't shared
    across projects, so either case means the id is simply wrong here.
    """
    groups = list(ShotGroup.objects.filter(project=project, pk__in=group_ids))
    found_ids = {group.id for group in groups}
    missing_ids = [group_id for group_id in group_ids if group_id not in found_ids]
    if missing_ids:
        raise APIError(
            controller.format_error(
                f"Shot group with id={missing_ids[0]} was not found in this project.",
                loc=["group_ids"],
                error_type=ErrorType.value_error,
            ),
            status_code=HTTPStatus.BAD_REQUEST,
        )
    return groups


class ShotListController(Controller[PydanticSerializer]):
    """`GET/POST /api/v1/projects/<project_id>/shots/` - list every shot in
    a project (regardless of group) and create new shots.

    This is the only shot-creation endpoint - see `ShotCreateIn` for why
    there's no corresponding create on the group-scoped collection.
    """

    request: AuthenticatedHttpRequest[User]
    auth = (access_token_auth,)

    @modify(
        summary="List a project's shots",
        description=(
            "Return a paginated list of every shot in the given project, "
            "regardless of which group(s) it belongs to, optionally "
            "filtered by `search` against the name."
        ),
        response_description="A page of shots.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
        ],
        tags=["Shots"],
    )
    def get(
        self,
        parsed_path: Path[ProjectShotsPath],
        parsed_query: Query[ShotListQuery],
    ) -> ShotListOut:
        project = _get_project_or_404(self.request.user, parsed_path.project_id)

        queryset = Shot.objects.filter(project=project)

        if parsed_query.search:
            queryset = queryset.filter(name__icontains=parsed_query.search)

        paginator = Paginator(queryset, parsed_query.page_size)
        page = paginator.get_page(parsed_query.page)

        return ShotListOut(
            items=[_serialize_shot(self.request, shot) for shot in page.object_list],
            total=paginator.count,
            page=parsed_query.page,
            page_size=parsed_query.page_size,
        )

    @modify(
        status_code=HTTPStatus.CREATED,
        summary="Create a shot",
        description=(
            "Create a new shot within the project, optionally placing it "
            "into one or more existing shot groups via `group_ids`. A "
            "shot may belong to zero, one, or several groups - there is "
            "no default group."
        ),
        response_description="The created shot.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
            ResponseSpec(dict, status_code=HTTPStatus.BAD_REQUEST),
        ],
        tags=["Shots"],
    )
    def post(
        self,
        parsed_path: Path[ProjectShotsPath],
        parsed_body: Body[ShotCreateIn],
    ) -> ShotOut:
        project = _get_project_or_404(self.request.user, parsed_path.project_id)

        if Shot.objects.filter(project=project, name=parsed_body.name).exists():
            raise APIError(
                self.format_error(
                    "A shot with this name already exists in this project.",
                    loc=["name"],
                    error_type=ErrorType.value_error,
                ),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        groups = _resolve_group_ids(self, project, parsed_body.group_ids)

        shot = Shot.objects.create(
            project=project,
            name=parsed_body.name,
            rec_timecode=parsed_body.rec_timecode,
            duration=parsed_body.duration,
            created_by=self.request.user,
            updated_by=self.request.user,
        )
        if groups:
            shot.groups.set(groups)

        return _serialize_shot(self.request, shot)


class ShotGroupShotListController(Controller[PydanticSerializer]):
    """`GET /api/v1/shot-groups/<id>/shots/` - list the shots belonging to
    a single group. Read-only - shots are created via
    `ShotListController`, not here.
    """

    request: AuthenticatedHttpRequest[User]
    auth = (access_token_auth,)

    @modify(
        summary="List a shot group's shots",
        description=(
            "Return a paginated list of shots belonging to the given "
            "group, optionally filtered by `search` against the name."
        ),
        response_description="A page of shots.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
        ],
        tags=["Shots"],
    )
    def get(
        self,
        parsed_path: Path[ShotGroupShotsPath],
        parsed_query: Query[ShotListQuery],
    ) -> ShotListOut:
        shot_group = _get_shot_group_or_404(
            self.request.user, parsed_path.shot_group_id
        )

        queryset = Shot.objects.filter(groups=shot_group)

        if parsed_query.search:
            queryset = queryset.filter(name__icontains=parsed_query.search)

        paginator = Paginator(queryset, parsed_query.page_size)
        page = paginator.get_page(parsed_query.page)

        return ShotListOut(
            items=[_serialize_shot(self.request, shot) for shot in page.object_list],
            total=paginator.count,
            page=parsed_query.page,
            page_size=parsed_query.page_size,
        )


class ShotDetailController(Controller[PydanticSerializer]):
    """`GET/PATCH/DELETE /api/v1/shots/<id>/` - manage a single shot."""

    request: AuthenticatedHttpRequest[User]
    auth = (access_token_auth,)

    @modify(
        summary="Get a shot",
        description="Return a single shot by id.",
        response_description="The requested shot.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
        ],
        tags=["Shots"],
    )
    def get(self, parsed_path: Path[ShotPath]) -> ShotOut:
        shot = _get_shot_or_404(self.request.user, parsed_path.shot_id)
        return _serialize_shot(self.request, shot)

    @modify(
        summary="Update a shot",
        description=(
            "Partially update a shot. `group_ids`, when present, replaces "
            "the full set of group memberships. `name` cannot be changed "
            "- it's immutable once set."
        ),
        response_description="The updated shot.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
            ResponseSpec(dict, status_code=HTTPStatus.BAD_REQUEST),
        ],
        tags=["Shots"],
    )
    def patch(
        self,
        parsed_path: Path[ShotPath],
        parsed_body: Body[ShotUpdateIn],
    ) -> ShotOut:
        shot = _get_shot_or_404(self.request.user, parsed_path.shot_id)

        update_fields = parsed_body.model_dump(
            exclude={"group_ids"}, exclude_unset=True
        )
        for field, value in update_fields.items():
            setattr(shot, field, value)
        if update_fields:
            shot.updated_by = self.request.user
            shot.save(update_fields=[*update_fields, "updated_by"])

        if "group_ids" in parsed_body.model_fields_set:
            groups = _resolve_group_ids(self, shot.project, parsed_body.group_ids or [])
            shot.groups.set(groups)

        return _serialize_shot(self.request, shot)

    @modify(
        status_code=HTTPStatus.NO_CONTENT,
        summary="Delete a shot",
        description="Permanently delete a shot.",
        extra_responses=[
            ResponseSpec(dict, status_code=HTTPStatus.NOT_FOUND),
        ],
        tags=["Shots"],
    )
    def delete(self, parsed_path: Path[ShotPath]) -> None:
        shot = _get_shot_or_404(self.request.user, parsed_path.shot_id)
        shot.delete()
        return None
