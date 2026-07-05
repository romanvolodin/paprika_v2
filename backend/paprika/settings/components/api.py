from dmr.openapi import OpenAPIConfig
from dmr.openapi.objects import Tag
from dmr.settings import Settings


DMR_SETTINGS = {
    Settings.openapi_config: OpenAPIConfig(
        title="Paprika API",
        version="1.0.0",
        description=("REST API for Paprika — a simple VFX task tracker."),
        tags=[
            Tag(
                name="Auth",
                description="Obtaining, refreshing, and revoking JWT tokens.",
            ),
            Tag(
                name="Users",
                description="Managing user accounts.",
            ),
        ],
    ),
}
