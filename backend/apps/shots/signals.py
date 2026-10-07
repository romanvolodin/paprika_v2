from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.companies.models import Company

from .models import ShotStatus


# (name, color, order) - entries with order=None are exception/side
# statuses (cancelled, on hold) that the frontend renders after a
# separator, not part of the primary ordered workflow. The first entry
# is the one seeded as `is_default`.
DEFAULT_SHOT_STATUSES = [
    ("Не начат", "#D40000", 0),
    ("В работе", "#FFAA00", 1),
    ("Готов", "#009900", 2),
    ("Есть комментарий", "#FF6600", 3),
    ("Принят", "#0088CC", 4),
    ("Отдан", "#7700BE", 5),
    ("Отмена", "#999999", None),
    ("На паузе", "#3d3d3d", None),
]


@receiver(post_save, sender=Company)
def seed_default_shot_statuses(sender, instance, created, **kwargs):
    """
    Give a newly created company a starter set of shot statuses.

    `Shot.status` is required and there's no per-project fallback (see
    the model docstrings for why that idea - which worked for
    `ShotGroup` - doesn't apply here), so a company needs *some*
    statuses, including a default, before any of its projects can have
    a shot at all. This is a signal rather than a call from
    `apps.companies`'s own view so that app stays unaware of `apps.shots`
    entirely - the dependency points the other way.
    """
    if not created:
        return

    default_name = DEFAULT_SHOT_STATUSES[0][0]
    ShotStatus.objects.bulk_create(
        ShotStatus(
            company=instance,
            name=name,
            color=color,
            order=order,
            is_default=(name == default_name),
            created_by=instance.created_by,
            updated_by=instance.created_by,
        )
        for name, color, order in DEFAULT_SHOT_STATUSES
    )
