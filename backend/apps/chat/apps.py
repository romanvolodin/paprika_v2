from django.apps import AppConfig


class ChatConfig(AppConfig):
    name = "apps.chat"

    def ready(self):
        from . import signals  # noqa: F401
