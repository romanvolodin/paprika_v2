import secrets

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import IntegrityError, models, transaction
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.core.models import BaseModel
from apps.projects.models import Project
from apps.shots.models import Shot, color_validator


abbreviation_validator = RegexValidator(
    regex=r"^[A-Z0-9]{2,5}$",
    message=_("Abbreviation must be 2-5 uppercase Latin letters or digits."),
)

_CODE_UNIQUE_CONSTRAINT = "unique_task_code_per_project"
_CODE_ATTEMPTS = 20


def _random_number() -> int:
    """A random 4-digit number for a task code (1000-9999)."""
    return 1000 + secrets.randbelow(9000)


class TaskType(BaseModel):
    """
    A company-defined kind of work (e.g. "Клинап", "Композ") that tasks
    are classified by.

    Lives at the company level so a studio's vocabulary is shared by all
    its projects (and a project template can start from a predefined
    set). Classifying tasks is what makes questions like "show me every
    shot that has clean-up work" answerable.

    `abbreviation` becomes the prefix of the public code of every task
    of this type (`CLN` -> `CLN4821`). It can be renamed later: codes of
    already created tasks never change.

    A type that tasks still use can't be deleted (`on_delete=PROTECT`
    on `Task.type`) - those tasks have to be moved to another type
    first. See `apps.tasks.signals` for the starter set a new company
    gets.
    """

    company = models.ForeignKey(
        Company,
        verbose_name=_("company"),
        on_delete=models.CASCADE,
        related_name="task_types",
    )
    name = models.CharField(_("name"), max_length=255)
    abbreviation = models.CharField(
        _("abbreviation"),
        max_length=5,
        validators=[abbreviation_validator],
        help_text=_("Prefix of task codes of this type, e.g. CLN."),
    )
    color = models.CharField(_("color"), max_length=7, validators=[color_validator])

    class Meta:
        verbose_name = _("task type")
        verbose_name_plural = _("task types")
        ordering = ["company", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"], name="unique_task_type_name_per_company"
            ),
            models.UniqueConstraint(
                fields=["company", "abbreviation"],
                name="unique_task_type_abbreviation_per_company",
            ),
        ]

    def __str__(self):
        return f"{self.company} — {self.name}"

    def __repr__(self):
        return (
            f"<TaskType id={self.id} name={self.name} "
            f"abbreviation={self.abbreviation} company_id={self.company_id}>"
        )


class TaskStatus(BaseModel):
    """
    A company-defined status a task can be in on a shot (e.g. "Не
    начата", "В работе", "Готова").

    Deliberately a separate model from `apps.shots.models.ShotStatus`
    although it works the same way: the workflow of a unit of work and
    the workflow of a shot differ ("Отдан" makes sense for a shot, not
    for a task). Lives at the company level, `order` is empty for side
    states ("Отмена", "На паузе") and exactly one status per company is
    `is_default` - enforced in the API layer by swapping, not by a
    constraint. See `ShotStatus` for the longer reasoning behind each of
    these choices.
    """

    company = models.ForeignKey(
        Company,
        verbose_name=_("company"),
        on_delete=models.CASCADE,
        related_name="task_statuses",
    )
    name = models.CharField(_("name"), max_length=255)
    color = models.CharField(_("color"), max_length=7, validators=[color_validator])
    order = models.IntegerField(
        _("order"),
        null=True,
        blank=True,
        help_text=_(
            "Sort position among the primary workflow statuses. Leave "
            "blank for an exception/side status (e.g. cancelled, on "
            "hold) that isn't part of the main sequence."
        ),
    )
    is_default = models.BooleanField(_("default"), default=False)

    class Meta:
        verbose_name = _("task status")
        verbose_name_plural = _("task statuses")
        ordering = ["company", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"], name="unique_task_status_name_per_company"
            )
        ]

    def __str__(self):
        return f"{self.company} — {self.name}"

    def __repr__(self):
        return (
            f"<TaskStatus id={self.id} name={self.name} "
            f"company_id={self.company_id} is_default={self.is_default}>"
        )


class Task(BaseModel):
    """
    A concrete piece of work that has to be done, e.g. "Замена неба" or
    "Клинап тросов".

    A task belongs to a project and has a `type`. It may be linked to
    any number of shots through `ShotTask` (the same sky replacement on
    five shots is one task) or to none at all - a standalone task such
    as "Финальные титры". For now a standalone task only has a name, a
    type and a description; tracking its progress will be designed
    later.

    Everything about *doing* the work (status, assignee, estimated and
    actual hours) lives on `ShotTask`, per shot - not here.

    `code` is the public identifier: the type's abbreviation plus four
    random digits (`CLN4821`), unique within the project. It's generated
    on creation and never changes afterwards, even if the task's type is
    switched or the type's abbreviation is renamed.
    """

    project = models.ForeignKey(
        Project,
        verbose_name=_("project"),
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    type = models.ForeignKey(
        TaskType,
        verbose_name=_("type"),
        on_delete=models.PROTECT,
        related_name="tasks",
    )
    code = models.CharField(_("code"), max_length=16, editable=False)
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True)
    shots = models.ManyToManyField(
        Shot,
        verbose_name=_("shots"),
        through="ShotTask",
        related_name="tasks",
        blank=True,
    )

    class Meta:
        verbose_name = _("task")
        verbose_name_plural = _("tasks")
        # Newest first - the task somebody just created is the one
        # they're about to look for.
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "code"], name=_CODE_UNIQUE_CONSTRAINT
            )
        ]

    def save(self, *args, **kwargs):
        if self.code or not self._state.adding:
            return super().save(*args, **kwargs)

        # Generate the code on first save. Collisions are resolved by
        # simply trying another number: the unique constraint is the
        # judge, so a concurrent insert of the same code is handled too.
        for _attempt in range(_CODE_ATTEMPTS):
            self.code = f"{self.type.abbreviation}{_random_number()}"
            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError as exc:
                if _CODE_UNIQUE_CONSTRAINT not in str(exc):
                    raise
        self.code = ""
        raise RuntimeError("Could not generate a unique task code.")

    def __str__(self):
        return f"{self.code} {self.name}"

    def __repr__(self):
        return f"<Task id={self.id} code={self.code} project_id={self.project_id}>"


class ShotTask(BaseModel):
    """
    A `Task` placed on a `Shot` - and everything about doing it there.

    Besides linking the two, this is where the work is tracked: the
    task's `status` on this shot, who it's `assignee`d to, and the
    estimated and actual hours. So the same task can be finished on one
    shot, in progress on another and assigned to different people.

    The task and the shot must belong to the same project (checked by
    the API - a database constraint can't span two tables), and a task
    can be placed on a given shot only once.

    `status` uses `on_delete=PROTECT` for the same reason as
    `Shot.status`: a status that's in use can't be deleted.
    """

    task = models.ForeignKey(
        Task,
        verbose_name=_("task"),
        on_delete=models.CASCADE,
        related_name="shot_tasks",
    )
    shot = models.ForeignKey(
        Shot,
        verbose_name=_("shot"),
        on_delete=models.CASCADE,
        related_name="shot_tasks",
    )
    status = models.ForeignKey(
        TaskStatus,
        verbose_name=_("status"),
        on_delete=models.PROTECT,
        related_name="shot_tasks",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("assignee"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_shot_tasks",
    )
    estimated_hours = models.DecimalField(
        _("estimated hours"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    actual_hours = models.DecimalField(
        _("actual hours"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = _("shot task")
        verbose_name_plural = _("shot tasks")
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["task", "shot"], name="unique_task_per_shot"
            )
        ]

    def __str__(self):
        return f"{self.task.code} on {self.shot.name}"

    def __repr__(self):
        return f"<ShotTask id={self.id} task_id={self.task_id} shot_id={self.shot_id}>"
