import re

from django.core.files.storage import default_storage
import pytest


pytestmark = pytest.mark.django_db


class TestAttachmentPaths:
    def test_file_goes_to_the_dated_chat_folder_of_its_shot(
        self, attachment_factory, shot_factory, project_factory, mocker
    ):
        mocker.patch("apps.chat.models.upload_date", return_value="2026-10-08")
        project = project_factory(code="PRJ")
        shot = shot_factory(project=project, name="PRJ_0010")

        attachment = attachment_factory(shot=shot, filename="photo.jpg")

        assert re.fullmatch(
            rf"{project.company.storage_token}/PRJ/shots/PRJ_0010/chat/2026-10-08"
            r"/photo-[a-z0-9]{8}\.jpg",
            attachment.file.name,
        )

    def test_the_same_name_uploaded_twice_does_not_clash(
        self, attachment_factory, shot
    ):
        first = attachment_factory(shot=shot, filename="photo.jpg")
        second = attachment_factory(shot=shot, filename="photo.jpg")

        assert first.file.name != second.file.name
        assert default_storage.exists(first.file.name)
        assert default_storage.exists(second.file.name)

    def test_cyrillic_names_stay_readable(self, attachment_factory, shot):
        attachment = attachment_factory(shot=shot, filename="заметки по кадру.txt")

        assert re.search(r"/заметки_по_кадру-[a-z0-9]{8}\.txt$", attachment.file.name)

    def test_the_original_name_is_kept_in_the_database(self, attachment_factory, shot):
        attachment = attachment_factory(shot=shot, filename="заметки по кадру.txt")

        attachment.refresh_from_db()
        assert attachment.filename == "заметки по кадру.txt"

    def test_a_name_without_an_extension(self, attachment_factory, shot):
        attachment = attachment_factory(shot=shot, filename="noext")

        assert re.search(r"/noext-[a-z0-9]{8}$", attachment.file.name)


class TestAttachmentCleanup:
    def test_deleting_the_last_attachment_removes_the_folders(
        self, attachment_factory, django_capture_on_commit_callbacks
    ):
        attachment = attachment_factory()
        shot_folder = attachment.file.name.split("/chat/")[0]
        assert default_storage.exists(shot_folder)

        with django_capture_on_commit_callbacks(execute=True):
            attachment.delete()

        assert not default_storage.exists(shot_folder)

    def test_other_attachments_of_the_shot_survive(
        self, attachment_factory, shot, django_capture_on_commit_callbacks
    ):
        first = attachment_factory(shot=shot)
        second = attachment_factory(shot=shot)

        with django_capture_on_commit_callbacks(execute=True):
            first.delete()

        assert not default_storage.exists(first.file.name)
        assert default_storage.exists(second.file.name)
