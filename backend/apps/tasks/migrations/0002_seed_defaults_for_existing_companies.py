# Companies created before this app existed never went through the
# `post_save` seeding signal (see `apps.tasks.signals`), so they have no
# task statuses or types - and without a default status no task could be
# placed on a shot. Give each of them the same starter set, but only if
# they have none yet, so the migration is safe to re-run.
#
# The starter data is duplicated here on purpose: a migration must keep
# working even if the signal's lists change later.

from django.db import migrations


STATUSES = [
    ("Не начата", "#D40000", 0),
    ("В работе", "#FFAA00", 1),
    ("Готова", "#009900", 2),
    ("Отмена", "#999999", None),
    ("На паузе", "#3d3d3d", None),
]
TYPES = [
    ("Композ", "COMP", "#7700BE"),
    ("Клинап", "CLN", "#009900"),
    ("Трекинг", "TRK", "#FFAA00"),
    ("Ротоскоп", "ROTO", "#D40000"),
]


def seed_existing_companies(apps, schema_editor):
    Company = apps.get_model("companies", "Company")
    TaskStatus = apps.get_model("tasks", "TaskStatus")
    TaskType = apps.get_model("tasks", "TaskType")

    for company in Company.objects.all():
        if not TaskStatus.objects.filter(company=company).exists():
            TaskStatus.objects.bulk_create(
                TaskStatus(
                    company=company,
                    name=name,
                    color=color,
                    order=order,
                    is_default=(name == STATUSES[0][0]),
                )
                for name, color, order in STATUSES
            )
        if not TaskType.objects.filter(company=company).exists():
            TaskType.objects.bulk_create(
                TaskType(
                    company=company, name=name, abbreviation=abbreviation, color=color
                )
                for name, abbreviation, color in TYPES
            )


class Migration(migrations.Migration):
    dependencies = [
        ("companies", "0001_initial"),
        ("tasks", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_existing_companies, migrations.RunPython.noop),
    ]
