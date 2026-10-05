from dmr.routing import Router, path

from .views import ShotGroupDetailController, ShotGroupListController


router = Router(
    "",
    [
        path(
            "projects/<int:project_id>/shot-groups/",
            ShotGroupListController.as_view(),
            name="shot-group-list",
        ),
        path(
            "shot-groups/<int:shot_group_id>/",
            ShotGroupDetailController.as_view(),
            name="shot-group-detail",
        ),
    ],
)
