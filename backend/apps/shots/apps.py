from django.apps import AppConfig


class ShotsConfig(AppConfig):
    name = "apps.shots"

    def ready(self):
        from . import signals  # noqa: F401
