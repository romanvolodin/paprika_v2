from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    name = "apps.projects"

    def ready(self):
        from . import signals  # noqa: F401
