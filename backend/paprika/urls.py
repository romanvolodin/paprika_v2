from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from dmr.openapi import build_schema
from dmr.openapi.views import OpenAPIJsonView, SwaggerView
from dmr.routing import Router

from apps.auth.api.urls import router as auth_router
from apps.companies.api.urls import router as companies_router
from apps.users.api.urls import router as users_router


api_router = Router("api/v1/")
api_router.include(auth_router)
api_router.include(companies_router)
api_router.include(users_router)

schema = build_schema(api_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    api_router.to_urlpatterns(namespace="api"),
    path(
        "api/v1/docs/openapi.json",
        OpenAPIJsonView.as_view(schema),
        name="openapi",
    ),
    path("api/v1/docs/", SwaggerView.as_view(schema), name="swagger"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
