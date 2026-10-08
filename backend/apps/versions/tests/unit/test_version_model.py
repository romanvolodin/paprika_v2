from django.db import IntegrityError, transaction
import pytest

from apps.versions.models import Version


pytestmark = pytest.mark.django_db


class TestVersionModel:
    def test_project_is_filled_in_from_the_shot(self, shot_factory, version_factory):
        shot = shot_factory()
        version = Version(
            shot=shot,
            name="PRJ_0010_v01",
            type=Version.Type.IMAGE,
            width=1,
            height=1,
            file_size=1,
            source="versions/x/a.jpg",
        )

        version.save()

        assert version.project_id == shot.project_id

    def test_name_is_unique_within_a_project(self, shot_factory, version_factory):
        project_shot_a = shot_factory()
        project_shot_b = shot_factory(project=project_shot_a.project)
        version_factory(shot=project_shot_a, name="PRJ_0010_v01")

        with pytest.raises(IntegrityError), transaction.atomic():
            version_factory(shot=project_shot_b, name="PRJ_0010_v01")

    def test_same_name_is_fine_in_another_project(self, version_factory):
        version_factory(name="PRJ_0010_v01")

        version_factory(name="PRJ_0010_v01")  # different project via new shot

        assert Version.objects.filter(name="PRJ_0010_v01").count() == 2

    def test_newest_version_comes_first(self, shot, version_factory):
        first = version_factory(shot=shot)
        second = version_factory(shot=shot)

        assert list(Version.objects.filter(shot=shot)) == [second, first]

    def test_str_is_the_name(self, version_factory):
        assert str(version_factory(name="PRJ_0010_v01")) == "PRJ_0010_v01"


class TestFileCleanup:
    def test_deleting_a_version_removes_its_files(
        self, version, django_capture_on_commit_callbacks
    ):
        storage = version.source.storage
        names = [version.source.name, version.thumb.name]
        assert all(storage.exists(name) for name in names)

        with django_capture_on_commit_callbacks(execute=True):
            version.delete()

        assert not any(storage.exists(name) for name in names)

    def test_deleting_a_shot_removes_its_versions_and_their_files(
        self, version, django_capture_on_commit_callbacks
    ):
        storage = version.source.storage
        name = version.source.name

        with django_capture_on_commit_callbacks(execute=True):
            version.shot.delete()

        assert not Version.objects.filter(pk=version.pk).exists()
        assert not storage.exists(name)

    def test_files_survive_until_the_transaction_commits(self, version):
        storage = version.source.storage
        name = version.source.name

        version.delete()  # inside the test's transaction: on_commit not run

        assert storage.exists(name)
