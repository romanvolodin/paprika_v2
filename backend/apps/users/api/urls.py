from dmr.routing import Router, path

from .views import MeController, UserDetailController, UserListController


router = Router(
    "",
    [
        path(
            "users/",
            UserListController.as_view(),
            name="user-list",
        ),
        path(
            "users/me/",
            MeController.as_view(),
            name="me",
        ),
        path(
            "users/<int:user_id>/",
            UserDetailController.as_view(),
            name="user-detail",
        ),
    ],
)
