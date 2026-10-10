import re

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import pytest

from apps.users.models import User


pytestmark = pytest.mark.django_db


def _give_avatar(user, name="me.png"):
    user.avatar = ContentFile(b"x", name=name)
    user.save()
    return user


class TestAvatarPaths:
    def test_avatar_goes_to_the_users_folder(self, user_factory):
        user = _give_avatar(user_factory())

        assert re.fullmatch(
            rf"users/{user.pk}/avatar/me-[a-z0-9]{{8}}\.png", user.avatar.name
        )

    def test_the_original_name_is_kept_with_a_token_added(self, user_factory):
        user = _give_avatar(user_factory(), name="Моя Фотка.JPG")

        assert re.fullmatch(
            rf"users/{user.pk}/avatar/Моя_Фотка-[a-z0-9]{{8}}\.JPG", user.avatar.name
        )

    def test_the_same_name_uploaded_twice_does_not_clash(self, user_factory):
        user = _give_avatar(user_factory(), name="me.png")
        first = user.avatar.name

        _give_avatar(user, name="me.png")

        assert user.avatar.name != first
        assert default_storage.exists(first)

    def test_a_new_avatar_gets_a_new_url(self, user_factory):
        user = _give_avatar(user_factory())
        old = user.avatar.name

        _give_avatar(user)

        assert user.avatar.name != old

    def test_a_user_that_is_not_saved_yet_goes_to_the_new_folder(self, user_factory):
        user = user_factory.build()
        user.avatar = ContentFile(b"x", name="me.png")

        user.avatar.save("me.png", ContentFile(b"x"), save=False)

        assert re.fullmatch(r"users/new/avatar/me-[a-z0-9]{8}\.png", user.avatar.name)


class TestAvatarCleanup:
    def test_deleting_a_user_removes_the_avatar_and_its_folders(
        self, user_factory, django_capture_on_commit_callbacks
    ):
        user = _give_avatar(user_factory())
        name = user.avatar.name

        with django_capture_on_commit_callbacks(execute=True):
            user.delete()

        assert not User.objects.filter(pk=user.pk).exists()
        assert not default_storage.exists(name)
        assert not default_storage.exists(f"users/{user.pk}")

    def test_a_user_without_an_avatar_can_be_deleted(
        self, user_factory, django_capture_on_commit_callbacks
    ):
        user = user_factory()

        with django_capture_on_commit_callbacks(execute=True):
            user.delete()

        assert not User.objects.filter(pk=user.pk).exists()
