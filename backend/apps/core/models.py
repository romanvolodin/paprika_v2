from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """
    Abstract base model providing common fields.

    `created_by`/`updated_by` are not filled automatically — the caller
    (controller/service) is responsible for passing the current user
    explicitly, since there is no reliable "current user" in background
    tasks (Celery) and thread-local middleware tricks are hard to test.
    """

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    created_by = models.ForeignKey(
        "users.User",
        verbose_name=_("created by"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        "users.User",
        verbose_name=_("updated by"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        abstract = True
