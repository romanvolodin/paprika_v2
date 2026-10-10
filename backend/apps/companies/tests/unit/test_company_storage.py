import re

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import pytest

from apps.companies.models import Company
from apps.companies.storage import marker_filename, sync_marker


pytestmark = pytest.mark.django_db


def _folder(company) -> tuple[list[str], list[str]]:
    return default_storage.listdir(company.storage_token)


class TestStorageToken:
    def test_is_generated_on_creation(self, company_factory):
        company = company_factory()

        assert re.fullmatch(r"[a-z0-9]{8}", company.storage_token)

    def test_is_different_for_every_company(self, company_factory):
        tokens = {company_factory().storage_token for _ in range(10)}

        assert len(tokens) == 10

    def test_does_not_change_when_the_company_is_renamed(self, company_factory):
        company = company_factory(name="Acme")
        token = company.storage_token

        company.name = "Acme Studios"
        company.save()
        company.refresh_from_db()

        assert company.storage_token == token

    def test_is_not_editable(self):
        assert Company._meta.get_field("storage_token").editable is False


class TestMarkerFilename:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("Acme", ".Acme"),
            ("Acme Studios", ".Acme_Studios"),
            ("Крутая студия", ".Крутая_студия"),
            ("../evil", "._evil"),
            ("...", ".company"),
            ("", ".company"),
        ],
    )
    def test_is_a_hidden_safe_file_name(self, company_factory, name, expected):
        company = company_factory.build(name=name)

        assert marker_filename(company) == expected


class TestMarkerFile:
    def test_is_created_with_the_company(
        self, company_factory, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            company = company_factory(name="Acme Studios")

        assert _folder(company) == ([], [".Acme_Studios"])

    def test_is_an_empty_file(
        self, company_factory, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            company = company_factory(name="Acme")

        assert default_storage.size(f"{company.storage_token}/.Acme") == 0

    def test_is_not_written_before_the_commit(self, company_factory):
        company = company_factory(name="Acme")  # inside the test transaction

        assert not default_storage.exists(company.storage_token)

    def test_is_renamed_with_the_company(
        self, company_factory, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            company = company_factory(name="Acme")

        with django_capture_on_commit_callbacks(execute=True):
            company.name = "Acme Studios"
            company.save()

        assert _folder(company) == ([], [".Acme_Studios"])

    def test_saving_without_a_rename_changes_nothing(
        self, company_factory, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            company = company_factory(name="Acme")

        with django_capture_on_commit_callbacks(execute=True):
            company.save()

        assert _folder(company) == ([], [".Acme"])

    def test_is_restored_if_it_went_missing(
        self, company_factory, django_capture_on_commit_callbacks
    ):
        company = company_factory(name="Acme")

        sync_marker(company)
        default_storage.delete(f"{company.storage_token}/.Acme")
        sync_marker(company)

        assert _folder(company) == ([], [".Acme"])

    def test_other_files_in_the_folder_are_left_alone(
        self, company_factory, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            company = company_factory(name="Acme")
        default_storage.save(
            f"{company.storage_token}/PRJ/cover.png", ContentFile(b"x")
        )

        with django_capture_on_commit_callbacks(execute=True):
            company.name = "Acme Studios"
            company.save()

        dirs, files = _folder(company)
        assert dirs == ["PRJ"]
        assert files == [".Acme_Studios"]

    def test_a_failure_does_not_break_the_save(
        self, company_factory, django_capture_on_commit_callbacks, mocker, caplog
    ):
        mocker.patch(
            "apps.companies.signals.sync_marker", side_effect=OSError("disk full")
        )

        with django_capture_on_commit_callbacks(execute=True):
            company = company_factory(name="Acme")

        assert Company.objects.filter(pk=company.pk).exists()
        assert "Could not update the media marker" in caplog.text

    def test_deleting_the_company_removes_its_folder(
        self, company_factory, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            company = company_factory(name="Acme")

        with django_capture_on_commit_callbacks(execute=True):
            company.delete()

        assert not default_storage.exists(company.storage_token)

    def test_deleting_the_company_keeps_a_folder_that_still_holds_files(
        self, company_factory, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            company = company_factory(name="Acme")
        default_storage.save(f"{company.storage_token}/stray.txt", ContentFile(b"x"))

        with django_capture_on_commit_callbacks(execute=True):
            company.delete()

        assert default_storage.exists(f"{company.storage_token}/stray.txt")
