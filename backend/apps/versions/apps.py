from django.apps import AppConfig


class VersionsConfig(AppConfig):
    name = "apps.versions"

    def ready(self):
        from . import signals  # noqa: F401
