import re

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import pytest

from apps.projects.models import Project


pytestmark = pytest.mark.django_db


def _give_cover(project, name="cover.png"):
    project.cover = ContentFile(b"x", name=name)
    project.save()
    return project


class TestCoverPaths:
    def test_cover_goes_to_the_project_folder(self, project_factory):
        project = _give_cover(project_factory(code="PRJ"))

        assert re.fullmatch(
            rf"{project.company.storage_token}/PRJ/cover-[a-z0-9]{{8}}\.png",
            project.cover.name,
        )

    def test_the_original_name_is_kept_with_a_token_added(self, project_factory):
        project = _give_cover(project_factory(code="PRJ"), name="Постер фильма.PNG")

        assert re.fullmatch(
            rf"{project.company.storage_token}/PRJ/Постер_фильма-[a-z0-9]{{8}}\.PNG",
            project.cover.name,
        )

    def test_a_new_cover_gets_a_new_url(self, project_factory):
        project = _give_cover(project_factory())
        old = project.cover.name

        _give_cover(project)

        assert project.cover.name != old

    def test_unsafe_project_codes_are_not_a_problem(self, project_factory):
        project = _give_cover(project_factory(code="A B/C"))

        assert re.fullmatch(
            rf"{project.company.storage_token}/A_B_C/cover-[a-z0-9]{{8}}\.png",
            project.cover.name,
        )


class TestCoverCleanup:
    def test_deleting_a_project_removes_the_cover_and_its_folder(
        self, project_factory, django_capture_on_commit_callbacks
    ):
        project = _give_cover(project_factory(code="PRJ"))
        name = project.cover.name

        with django_capture_on_commit_callbacks(execute=True):
            project.delete()

        assert not Project.objects.filter(pk=project.pk).exists()
        assert not default_storage.exists(name)

    def test_deleting_a_company_removes_the_covers_of_its_projects(
        self, project_factory, django_capture_on_commit_callbacks
    ):
        project = _give_cover(project_factory())
        name = project.cover.name

        with django_capture_on_commit_callbacks(execute=True):
            project.company.delete()

        assert not default_storage.exists(name)
