from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from dmr.openapi import build_schema
from dmr.openapi.views import OpenAPIJsonView, SwaggerView
from dmr.routing import Router

from apps.auth.api.urls import router as auth_router
from apps.users.api.urls import router as users_router


app_routers = (
    auth_router,
    users_router,
)

api_router = Router(
    "api/v1/",
    [url for app_router in app_routers for url in app_router.urls],
)

schema = build_schema(api_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path(api_router.prefix, include((api_router.urls, "api"))),
    path(
        "api/v1/docs/openapi.json",
        OpenAPIJsonView.as_view(schema),
        name="openapi",
    ),
    path("api/v1/docs/", SwaggerView.as_view(schema), name="swagger"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
