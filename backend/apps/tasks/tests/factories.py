import factory
from factory.django import DjangoModelFactory

from apps.tasks.models import ShotTask, Task, TaskStatus, TaskType


class TaskTypeFactory(DjangoModelFactory):
    """Builds `TaskType` instances for tests.

    Note a new `Company` already comes with a starter set of task types
    (see `apps.tasks.signals`); this factory adds one more.

    Usage:
        task_type_factory()                  # saved, random company + name
        task_type_factory(company=company, name="Анимация", abbreviation="ANM")
    """

    class Meta:
        model = TaskType

    company = factory.SubFactory("apps.companies.tests.factories.CompanyFactory")
    name = factory.Sequence(lambda n: f"Task Type {n}")
    abbreviation = factory.Sequence(lambda n: f"T{n:03d}")
    color = "#FF5733"


class TaskStatusFactory(DjangoModelFactory):
    """Builds `TaskStatus` instances for tests.

    Usage:
        task_status_factory()                 # saved, random company + name
        task_status_factory(company=company, name="На ревью", color="#FFAA00")
    """

    class Meta:
        model = TaskStatus

    company = factory.SubFactory("apps.companies.tests.factories.CompanyFactory")
    name = factory.Sequence(lambda n: f"Task Status {n}")
    color = "#FF5733"
    order = None
    is_default = False


class TaskFactory(DjangoModelFactory):
    """Builds `Task` instances for tests (the `code` is generated on save).

    Usage:
        task_factory()                          # saved, standalone, random project
        task_factory(project=project, name="Замена неба")
        task_factory(type=some_type)            # override the default type
    """

    class Meta:
        model = Task

    project = factory.SubFactory("apps.projects.tests.factories.ProjectFactory")
    # A `Company` seeds a starter set of types, so reuse one of them
    # (scoped to the task's own project's company).
    type = factory.LazyAttribute(
        lambda o: (
            o.project.company.task_types.first()
            or TaskTypeFactory(company=o.project.company)
        )
    )
    name = factory.Sequence(lambda n: f"Task {n}")
    description = ""


class ShotTaskFactory(DjangoModelFactory):
    """Builds `ShotTask` instances for tests.

    The task is created in the shot's project and the status is the
    company's default one, so the result is consistent by default.

    Usage:
        shot_task_factory()                     # saved, random shot + task
        shot_task_factory(shot=shot, task=task, assignee=user)
        shot_task_factory(estimated_hours=4)
    """

    class Meta:
        model = ShotTask

    shot = factory.SubFactory("apps.shots.tests.factories.ShotFactory")
    task = factory.SubFactory(
        TaskFactory, project=factory.SelfAttribute("..shot.project")
    )
    status = factory.LazyAttribute(
        lambda o: (
            o.shot.project.company.task_statuses.filter(is_default=True).first()
            or TaskStatusFactory(company=o.shot.project.company)
        )
    )
