from dmr.routing import Router, path

from .views import VersionDetailController, VersionListController


router = Router(
    "",
    [
        path(
            "shots/<int:shot_id>/versions/",
            VersionListController.as_view(),
            name="version-list",
        ),
        path(
            "versions/<int:version_id>/",
            VersionDetailController.as_view(),
            name="version-detail",
        ),
    ],
)
