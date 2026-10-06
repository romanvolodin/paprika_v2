from django.core.validators import MinValueValidator
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


class Shot(BaseModel):
    """
    A single shot within a project.

    Belongs directly to a `Project` (not just transitively through its
    groups) because its name is unique at the project level, not the
    group level - a shot's identity doesn't depend on which group(s) it
    happens to be filed under.

    `groups` is a separate, optional, many-to-many concern: a shot can
    belong to zero, one, or several `ShotGroup`s of the same project
    simultaneously (membership in several groups is a deliberate, real
    use case, not an edge case to guard against). There's no "default"
    or "all" group auto-created for ungrouped shots - ungrouped is
    simply an empty `groups` set, and "every shot in this project" is
    already answered by filtering on `project` directly.

    Like `Project.code`, `name` is set once and never renamed - see
    spec-decisions on the public id scheme (`{project.code}_{shot.name}`).
    """

    project = models.ForeignKey(
        Project,
        verbose_name=_("project"),
        on_delete=models.CASCADE,
        related_name="shots",
    )
    groups = models.ManyToManyField(
        ShotGroup,
        verbose_name=_("groups"),
        blank=True,
        related_name="shots",
    )
    name = models.CharField(_("name"), max_length=255)
    rec_timecode = models.IntegerField(
        _("record timecode"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_("Start position of the shot in the edit, in frames."),
    )
    duration = models.IntegerField(
        _("duration"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text=_("Length of the shot, in frames."),
    )

    class Meta:
        verbose_name = _("shot")
        verbose_name_plural = _("shots")
        ordering = ["project", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"], name="unique_shot_name_per_project"
            )
        ]

    def __str__(self):
        return f"{self.project} — {self.name}"

    def __repr__(self):
        return f"<Shot id={self.id} name={self.name} project_id={self.project_id}>"
