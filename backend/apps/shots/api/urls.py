from dmr.routing import Router, path

from .views import (
    ShotDetailController,
    ShotGroupDetailController,
    ShotGroupListController,
    ShotGroupShotListController,
    ShotListController,
)


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
        path(
            "projects/<int:project_id>/shots/",
            ShotListController.as_view(),
            name="shot-list",
        ),
        path(
            "shot-groups/<int:shot_group_id>/shots/",
            ShotGroupShotListController.as_view(),
            name="shot-group-shot-list",
        ),
        path(
            "shots/<int:shot_id>/",
            ShotDetailController.as_view(),
            name="shot-detail",
        ),
    ],
)
