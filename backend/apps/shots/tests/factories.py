import factory
from factory.django import DjangoModelFactory

from apps.shots.models import ShotGroup


class ShotGroupFactory(DjangoModelFactory):
    """Builds `ShotGroup` instances for tests.

    Usage:
        shot_group_factory()                        # saved, random project + name
        shot_group_factory(project=project, name="Int. Office")
        shot_group_factory.build(...)               # unsaved instance (no DB hit)
    """

    class Meta:
        model = ShotGroup

    project = factory.SubFactory("apps.projects.tests.factories.ProjectFactory")
    name = factory.Sequence(lambda n: f"Shot Group {n}")
