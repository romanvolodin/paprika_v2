from django.db import IntegrityError
import pytest

from apps.shots.models import ShotGroup


pytestmark = pytest.mark.django_db


class TestShotGroupModel:
    def test_str_contains_project_and_name(self, shot_group_factory, project_factory):
        project = project_factory(code="PRJ", name="Acme Feature")
        shot_group = shot_group_factory(project=project, name="Int. Office")

        # `Project.__str__` is itself "code — name", so this nests that.
        assert str(shot_group) == "PRJ — Acme Feature — Int. Office"

    def test_repr_contains_id_name_and_project_id(self, shot_group_factory, project):
        shot_group = shot_group_factory(project=project, name="Int. Office")

        text = repr(shot_group)

        assert f"id={shot_group.id}" in text
        assert "name=Int. Office" in text
        assert f"project_id={project.id}" in text

    def test_name_must_be_unique_within_project(self, shot_group_factory, project):
        shot_group_factory(project=project, name="Int. Office")

        with pytest.raises(IntegrityError):
            shot_group_factory(project=project, name="Int. Office")

    def test_same_name_allowed_in_different_projects(
        self, shot_group_factory, project_factory
    ):
        project_a = project_factory()
        project_b = project_factory()
        shot_group_factory(project=project_a, name="Int. Office")

        # Should not raise.
        shot_group_factory(project=project_b, name="Int. Office")

    def test_ordering_is_by_project_then_name(self, shot_group_factory, project):
        shot_group_factory(project=project, name="C Group")
        shot_group_factory(project=project, name="A Group")
        shot_group_factory(project=project, name="B Group")

        names = list(
            ShotGroup.objects.filter(project=project).values_list("name", flat=True)
        )

        assert names == sorted(names)

    def test_created_by_is_set_to_null_when_creator_is_deleted(
        self, shot_group_factory, user_factory
    ):
        creator = user_factory()
        shot_group = shot_group_factory(created_by=creator)

        creator.delete()
        shot_group.refresh_from_db()

        assert shot_group.created_by is None

    def test_is_deleted_when_project_is_deleted(self, shot_group_factory, project):
        shot_group = shot_group_factory(project=project)
        shot_group_id = shot_group.id

        project.delete()

        assert not ShotGroup.objects.filter(id=shot_group_id).exists()
