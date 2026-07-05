from dmr.routing import Router, path

from .views import MeController


router = Router(
    "",
    [
        path("users/me/", MeController.as_view(), name="me"),
    ],
)
