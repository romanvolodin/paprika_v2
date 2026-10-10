import re

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import pytest

from apps.versions.models import Version


pytestmark = pytest.mark.django_db

_TOKEN = r"[a-z0-9]{8}"


def _make(version_factory, shot, name):
    return version_factory(shot=shot, name=name)


class TestVersionPaths:
    def test_source_lives_in_the_shot_folder_of_its_project(
        self, shot_factory, version_factory, project_factory
    ):
        project = project_factory(code="PRJ")
        shot = shot_factory(project=project, name="PRJ_0010")

        version = _make(version_factory, shot, "PRJ_0010_v01")

        company_token = project.company.storage_token
        assert re.fullmatch(
            rf"{company_token}/PRJ/shots/PRJ_0010/versions/PRJ_0010_v01-{_TOKEN}"
            r"/PRJ_0010_v01\.jpg",
            version.source.name,
        )

    def test_thumb_is_next_to_the_source_and_named_after_it(
        self, shot, version_factory
    ):
        version = _make(version_factory, shot, "PRJ_0010_v01")

        source_dir, _, _ = version.source.name.rpartition("/")
        thumb_dir, _, thumb_name = version.thumb.name.rpartition("/")
        assert thumb_dir == source_dir
        assert thumb_name == "PRJ_0010_v01.jpg_thumb.jpg"

    def test_converted_file_goes_next_to_the_source_too(self, shot, version_factory):
        version = _make(version_factory, shot, "PRJ_0010_v01")

        version.converted = ContentFile(b"x", name="PRJ_0010_v01.jpg_converted.mp4")
        version.save()

        assert (
            version.converted.name.rpartition("/")[0]
            == (version.source.name.rpartition("/")[0])
        )
        assert version.converted.name.endswith("/PRJ_0010_v01.jpg_converted.mp4")

    def test_every_version_gets_its_own_token(self, shot, version_factory):
        first = _make(version_factory, shot, "PRJ_0010_v01")
        second = _make(version_factory, shot, "PRJ_0010_v02")

        assert (
            first.source.name.rpartition("/")[0]
            != (second.source.name.rpartition("/")[0])
        )

    def test_unsafe_names_become_safe_folders(
        self, shot_factory, version_factory, project_factory
    ):
        shot = shot_factory(project=project_factory(code="PRJ"), name="Кадр 1/2")

        version = _make(version_factory, shot, "v 01: final?")

        assert re.fullmatch(
            rf"{shot.project.company.storage_token}/PRJ/shots/Кадр_1_2"
            rf"/versions/v_01_final_-{_TOKEN}/v_01_final_\.jpg",
            version.source.name,
        )

    def test_shots_with_names_that_collapse_share_a_folder_without_clashing(
        self, shot_factory, version_factory, project_factory
    ):
        project = project_factory(code="PRJ")
        shot_a = shot_factory(project=project, name="A B")
        shot_b = shot_factory(project=project, name="A_B")

        first = _make(version_factory, shot_a, "PRJ_0010_v01")
        second = _make(version_factory, shot_b, "PRJ_0020_v01")

        assert (
            first.source.name.split("/versions/")[0]
            == (second.source.name.split("/versions/")[0])
        )
        assert first.source.name != second.source.name
        assert default_storage.exists(first.source.name)
        assert default_storage.exists(second.source.name)


class TestFolderCleanup:
    def test_deleting_the_only_version_removes_the_folders(
        self, version, django_capture_on_commit_callbacks
    ):
        shot_folder = version.source.name.split("/versions/")[0]
        assert default_storage.exists(shot_folder)

        with django_capture_on_commit_callbacks(execute=True):
            version.delete()

        assert not default_storage.exists(shot_folder)

    def test_deleting_one_version_keeps_the_others(
        self, shot, version_factory, django_capture_on_commit_callbacks
    ):
        first = _make(version_factory, shot, "PRJ_0010_v01")
        second = _make(version_factory, shot, "PRJ_0010_v02")

        with django_capture_on_commit_callbacks(execute=True):
            first.delete()

        assert not default_storage.exists(first.source.name)
        assert default_storage.exists(second.source.name)
        assert default_storage.exists(second.thumb.name)

    def test_deleting_a_project_removes_all_its_files(
        self, version, django_capture_on_commit_callbacks
    ):
        project = version.project
        company_folder = version.source.name.split("/")[0]

        with django_capture_on_commit_callbacks(execute=True):
            project.delete()

        assert not Version.objects.exists()
        assert not default_storage.exists(company_folder)
