import datetime
import re

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import pytest

from apps.core.storage import (
    MAX_FILENAME_LENGTH,
    MAX_SEGMENT_LENGTH,
    delete_on_commit,
    delete_stored_file,
    dir_with_token,
    file_with_token,
    make_token,
    prune_empty_dirs,
    sanitize_filename,
    sanitize_name,
    upload_date,
)


class TestMakeToken:
    def test_is_eight_lowercase_letters_and_digits(self):
        for _ in range(50):
            assert re.fullmatch(r"[a-z0-9]{8}", make_token())

    def test_differs_between_calls(self):
        assert len({make_token() for _ in range(50)}) == 50


class TestSanitizeName:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("PRJ_0010", "PRJ_0010"),
            ("PRJ_0010_v01", "PRJ_0010_v01"),
            ("PRJ 0010", "PRJ_0010"),
            ("Кадр 1", "Кадр_1"),
            ("a/b\\c", "a_b_c"),
            ("a  //  b", "a_b"),
            ("shot:01?*", "shot_01_"),
            ("a-b.c", "a-b.c"),
            (".hidden", "hidden"),
            ("..", "_"),
            ("...", "_"),
            ("name.", "name"),
            ("", "_"),
            ("***", "_"),
        ],
    )
    def test_makes_a_safe_segment(self, value, expected):
        assert sanitize_name(value) == expected

    def test_never_returns_a_path_traversal_segment(self):
        for value in ("..", "../..", "./", "/", "\\"):
            assert sanitize_name(value) not in ("", ".", "..")
            assert "/" not in sanitize_name(value)

    def test_is_cut_to_the_maximum_length(self):
        assert len(sanitize_name("a" * 500)) == MAX_SEGMENT_LENGTH

    def test_cut_name_does_not_end_with_a_dot(self):
        value = "a" * (MAX_SEGMENT_LENGTH - 1) + "." + "b" * 10

        assert not sanitize_name(value).endswith(".")

    def test_decomposed_unicode_is_normalised(self):
        decomposed = "и\u0306"  # "й" as two code points

        assert sanitize_name(decomposed) == "й"

    def test_is_idempotent(self):
        once = sanitize_name("Кадр №1 / финал?")

        assert sanitize_name(once) == once

    def test_different_names_may_collapse_into_one(self):
        # Accepted on purpose: the folders are merged, see the docs.
        assert sanitize_name("A B") == sanitize_name("A_B")


class TestSanitizeFilename:
    def test_keeps_a_normal_name(self):
        assert sanitize_filename("PRJ_0010_v01.mp4") == "PRJ_0010_v01.mp4"

    def test_keeps_the_double_extension_naming_of_derived_files(self):
        name = "PRJ_0010_v01.mov_thumb.jpg"

        assert sanitize_filename(name) == name

    def test_replaces_unsafe_characters(self):
        assert sanitize_filename("my file (1).png") == "my_file_1_.png"

    def test_drops_any_directories(self):
        assert sanitize_filename("../../etc/passwd") == "passwd"
        assert sanitize_filename("C:\\dir\\scene.nk") == "scene.nk"

    def test_name_without_an_extension(self):
        assert sanitize_filename("README") == "README"

    def test_trailing_dot_is_dropped(self):
        assert sanitize_filename("file.") == "file"

    def test_leading_dot_file(self):
        assert sanitize_filename(".bashrc") == "bashrc"

    def test_empty_name_gets_a_fallback(self):
        assert sanitize_filename("") == "file"
        assert sanitize_filename("???.txt") == "_.txt"

    def test_long_name_is_cut_but_keeps_its_extension(self):
        result = sanitize_filename("a" * 500 + ".mp4")

        assert len(result) == MAX_FILENAME_LENGTH
        assert result.endswith(".mp4")


class TestNamesWithTokens:
    def test_dir_with_token(self):
        assert re.fullmatch(r"PRJ_0010_v01-[a-z0-9]{8}", dir_with_token("PRJ_0010_v01"))

    def test_dir_with_token_sanitizes_the_name(self):
        assert re.fullmatch(r"Кадр_1-[a-z0-9]{8}", dir_with_token("Кадр 1"))

    def test_file_with_token_keeps_name_and_extension(self):
        assert re.fullmatch(r"photo-[a-z0-9]{8}\.jpg", file_with_token("photo.jpg"))

    def test_file_with_token_keeps_the_extension_as_uploaded(self):
        assert re.fullmatch(r"Photo-[a-z0-9]{8}\.JPG", file_with_token("Photo.JPG"))

    def test_file_with_token_keeps_the_whole_name(self):
        assert re.fullmatch(
            r"my_avatar_v2-[a-z0-9]{8}\.png", file_with_token("my_avatar_v2.png")
        )

    def test_file_with_token_drops_any_directories(self):
        assert re.fullmatch(r"passwd-[a-z0-9]{8}", file_with_token("../../etc/passwd"))

    def test_file_with_token_without_an_extension(self):
        assert re.fullmatch(r"noext-[a-z0-9]{8}", file_with_token("noext"))

    def test_same_name_gives_different_results(self):
        assert file_with_token("a.txt") != file_with_token("a.txt")

    def test_long_name_stays_within_the_limit(self):
        assert len(file_with_token("a" * 500 + ".txt")) <= MAX_FILENAME_LENGTH


class TestUploadDate:
    def test_formats_a_date(self):
        now = datetime.datetime(2026, 10, 8, 12, 0, tzinfo=datetime.UTC)

        assert upload_date(now) == "2026-10-08"

    def test_uses_utc_whatever_the_timezone_of_the_moment(self):
        moscow = datetime.timezone(datetime.timedelta(hours=3))
        now = datetime.datetime(2026, 10, 9, 1, 30, tzinfo=moscow)  # 22:30 UTC, 8th

        assert upload_date(now) == "2026-10-08"


class TestPruneEmptyDirs:
    def _save(self, name):
        return default_storage.save(name, ContentFile(b"x"))

    def test_removes_every_empty_parent(self):
        name = self._save("a/b/c/file.txt")
        default_storage.delete(name)

        prune_empty_dirs(default_storage, "a/b/c")

        assert not default_storage.exists("a")

    def test_stops_at_a_folder_that_still_holds_something(self):
        name = self._save("a/b/c/file.txt")
        self._save("a/other.txt")
        default_storage.delete(name)

        prune_empty_dirs(default_storage, "a/b/c")

        assert not default_storage.exists("a/b")
        assert default_storage.exists("a/other.txt")

    def test_leaves_a_folder_with_files_alone(self):
        self._save("a/b/one.txt")

        prune_empty_dirs(default_storage, "a/b")

        assert default_storage.exists("a/b/one.txt")

    def test_a_missing_folder_is_not_an_error(self):
        prune_empty_dirs(default_storage, "nothing/here")

    def test_a_marker_file_keeps_the_folder(self):
        self._save("company/.Acme")
        self._save("company/project/file.txt")
        default_storage.delete("company/project/file.txt")

        prune_empty_dirs(default_storage, "company/project")

        assert not default_storage.exists("company/project")
        assert default_storage.exists("company/.Acme")


class TestDeleteStoredFile:
    def test_deletes_the_file_and_its_empty_folders(self):
        name = default_storage.save("x/y/file.txt", ContentFile(b"x"))

        delete_stored_file(default_storage, name)

        assert not default_storage.exists("x")

    def test_keeps_folders_that_hold_other_files(self):
        first = default_storage.save("x/y/one.txt", ContentFile(b"x"))
        second = default_storage.save("x/y/two.txt", ContentFile(b"x"))

        delete_stored_file(default_storage, first)

        assert not default_storage.exists(first)
        assert default_storage.exists(second)

    def test_a_file_that_is_already_gone_is_not_an_error(self):
        delete_stored_file(default_storage, "x/y/missing.txt")


@pytest.mark.django_db
class TestDeleteOnCommit:
    def test_deletes_after_the_commit_only(self, django_capture_on_commit_callbacks):
        name = default_storage.save("x/file.txt", ContentFile(b"x"))

        class Field:
            storage = default_storage

        field = Field()
        field.name = name

        with django_capture_on_commit_callbacks(execute=False) as callbacks:
            delete_on_commit(field)
        assert default_storage.exists(name)

        for callback in callbacks:
            callback()
        assert not default_storage.exists(name)
        assert not default_storage.exists("x")

    def test_empty_fields_are_ignored(self, django_capture_on_commit_callbacks):
        class Field:
            storage = default_storage
            name = ""

        with django_capture_on_commit_callbacks(execute=False) as callbacks:
            delete_on_commit(Field(), None)

        assert callbacks == []
