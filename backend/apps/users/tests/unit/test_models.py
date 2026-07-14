import pytest

from apps.users.models import User


pytestmark = pytest.mark.django_db


class TestUserModel:
    def test_str_returns_email(self, user_factory):
        user = user_factory(email="someone@example.com")

        assert str(user) == "someone@example.com"

    def test_repr_contains_id_and_email(self, user_factory):
        user = user_factory(email="someone@example.com")

        assert f"id={user.id}" in repr(user)
        assert "email=someone@example.com" in repr(user)

    def test_get_full_name_joins_first_and_last(self, user_factory):
        user = user_factory(first_name="Jane", last_name="Doe")

        assert user.get_full_name() == "Jane Doe"

    def test_get_short_name_returns_first_name(self, user_factory):
        user = user_factory(first_name="Jane", last_name="Doe")

        assert user.get_short_name() == "Jane"

    def test_is_active_defaults_to_true(self, user_factory):
        user = user_factory()

        assert user.is_active is True

    def test_is_staff_defaults_to_false(self, user_factory):
        user = user_factory()

        assert user.is_staff is False

    def test_email_must_be_unique(self, user_factory):
        user_factory(email="dup@example.com")

        with pytest.raises(Exception):  # noqa: B017, PT011 - IntegrityError, DB-specific
            user_factory(email="dup@example.com")

    def test_avatar_is_blank_by_default(self, user_factory):
        user = user_factory()

        assert not user.avatar

    def test_ordering_is_by_email(self, user_factory):
        user_factory(email="c@example.com")
        user_factory(email="a@example.com")
        user_factory(email="b@example.com")

        emails = list(User.objects.values_list("email", flat=True))

        assert emails == sorted(emails)
