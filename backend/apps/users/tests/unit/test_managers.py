import pytest

from apps.users.models import User


pytestmark = pytest.mark.django_db


class TestCreateUser:
    def test_creates_a_user_with_a_usable_password(self):
        instance = User.objects.create_user(
            email="new@example.com",
            password="PassW0rd1",
            first_name="New",
            last_name="User",
        )

        assert instance.email == "new@example.com"
        assert instance.check_password("PassW0rd1")

    def test_normalizes_the_email_domain(self):
        instance = User.objects.create_user(
            email="someone@EXAMPLE.COM",
            password="PassW0rd1",
        )

        assert instance.email == "someone@example.com"

    def test_without_password_creates_unusable_password(self):
        instance = User.objects.create_user(email="invited@example.com")

        assert instance.has_usable_password() is False

    def test_without_email_raises(self):
        with pytest.raises(ValueError, match="Email"):
            User.objects.create_user(email="", password="PassW0rd1")

    def test_none_email_raises(self):
        with pytest.raises(ValueError, match="Email"):
            User.objects.create_user(email=None, password="PassW0rd1")


class TestCreateSuperuser:
    def test_creates_a_staff_superuser(self):
        instance = User.objects.create_superuser(
            email="admin@example.com",
            password="PassW0rd1",
        )

        assert instance.is_staff is True
        assert instance.is_superuser is True

    def test_requires_a_password(self):
        with pytest.raises(ValueError, match="password"):
            User.objects.create_superuser(email="admin@example.com", password=None)

    def test_rejects_is_staff_false(self):
        with pytest.raises(ValueError, match="is_staff"):
            User.objects.create_superuser(
                email="admin@example.com",
                password="PassW0rd1",
                is_staff=False,
            )

    def test_rejects_is_superuser_false(self):
        with pytest.raises(ValueError, match="is_superuser"):
            User.objects.create_superuser(
                email="admin@example.com",
                password="PassW0rd1",
                is_superuser=False,
            )
