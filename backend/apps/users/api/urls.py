from dmr.routing import Router, path

from .views import LoginController, LogoutController, MeController, RefreshController


router = Router(
    "",
    [
        path("auth/login/", LoginController.as_view(), name="login"),
        path("auth/logout/", LogoutController.as_view(), name="logout"),
        path("auth/refresh/", RefreshController.as_view(), name="refresh"),
        path("users/me/", MeController.as_view(), name="me"),
    ],
)
