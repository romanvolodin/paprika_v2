from dmr.routing import Router, path

from .views import (
    ProjectDetailController,
    ProjectListController,
    ProjectMemberDetailController,
    ProjectMemberListController,
)


router = Router(
    "",
    [
        path(
            "companies/<int:company_id>/projects/",
            ProjectListController.as_view(),
            name="project-list",
        ),
        path(
            "projects/<int:project_id>/",
            ProjectDetailController.as_view(),
            name="project-detail",
        ),
        path(
            "projects/<int:project_id>/members/",
            ProjectMemberListController.as_view(),
            name="project-member-list",
        ),
        path(
            "projects/<int:project_id>/members/<int:user_id>/",
            ProjectMemberDetailController.as_view(),
            name="project-member-detail",
        ),
    ],
)
