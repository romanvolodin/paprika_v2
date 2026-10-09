from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.companies.models import Company

from .models import TaskStatus, TaskType


# (name, color, order) - entries with order=None are side states shown
# after the main workflow. The first entry is seeded as `is_default`.
DEFAULT_TASK_STATUSES = [
    ("Не начата", "#D40000", 0),
    ("В работе", "#FFAA00", 1),
    ("Готова", "#009900", 2),
    ("Отмена", "#999999", None),
    ("На паузе", "#3d3d3d", None),
]

# (name, abbreviation, color)
DEFAULT_TASK_TYPES = [
    ("Композ", "COMP", "#7700BE"),
    ("Клинап", "CLN", "#009900"),
    ("Трекинг", "TRK", "#FFAA00"),
    ("Ротоскоп", "ROTO", "#D40000"),
]


@receiver(post_save, sender=Company)
def seed_default_task_statuses_and_types(sender, instance, created, **kwargs):
    """
    Give a newly created company a starter set of task statuses and
    task types.

    A `ShotTask` needs a status and a `Task` needs a type, so a company
    has to have some (including a default status) before its projects
    can have any tasks. A signal rather than a call from
    `apps.companies` keeps that app unaware of `apps.tasks` - the
    dependency points the other way (same approach as
    `apps.shots.signals`).
    """
    if not created:
        return

    default_name = DEFAULT_TASK_STATUSES[0][0]
    TaskStatus.objects.bulk_create(
        TaskStatus(
            company=instance,
            name=name,
            color=color,
            order=order,
            is_default=(name == default_name),
            created_by=instance.created_by,
            updated_by=instance.created_by,
        )
        for name, color, order in DEFAULT_TASK_STATUSES
    )
    TaskType.objects.bulk_create(
        TaskType(
            company=instance,
            name=name,
            abbreviation=abbreviation,
            color=color,
            created_by=instance.created_by,
            updated_by=instance.created_by,
        )
        for name, abbreviation, color in DEFAULT_TASK_TYPES
    )
