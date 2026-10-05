from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.projects.models import Project


class ShotGroup(BaseModel):
    """
    An arbitrary grouping of shots within a project.

    The grouping criterion is up to the team (sequence, location, asset,
    anything else) - deliberately named "group" rather than "sequence"
    so the name itself doesn't imply order or chronology. Visibility
    follows the parent project's `ProjectMembership`, same as `Project`
    itself - there's no separate membership model for groups.
    """

    project = models.ForeignKey(
        Project,
        verbose_name=_("project"),
        on_delete=models.CASCADE,
        related_name="shot_groups",
    )
    name = models.CharField(_("name"), max_length=255)

    class Meta:
        verbose_name = _("shot group")
        verbose_name_plural = _("shot groups")
        ordering = ["project", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"], name="unique_shot_group_name_per_project"
            )
        ]

    def __str__(self):
        return f"{self.project} — {self.name}"

    def __repr__(self):
        return f"<ShotGroup id={self.id} name={self.name} project_id={self.project_id}>"
