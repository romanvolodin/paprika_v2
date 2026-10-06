import factory
from factory.django import DjangoModelFactory

from apps.shots.models import Shot, ShotGroup


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


class ShotFactory(DjangoModelFactory):
    """Builds `Shot` instances for tests.

    Usage:
        shot_factory()                           # saved, random project/name, no groups
        shot_factory(project=project, name="0010")
        shot_factory(groups=[group_a, group_b])  # M2M set after creation
        shot_factory.build(...)                  # unsaved instance (no DB hit)
    """

    class Meta:
        model = Shot
        skip_postgeneration_save = True

    project = factory.SubFactory("apps.projects.tests.factories.ProjectFactory")
    name = factory.Sequence(lambda n: f"Shot {n}")

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.groups.set(extracted)
