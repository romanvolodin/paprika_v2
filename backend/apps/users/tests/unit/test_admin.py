from django.test import Client
from django.urls import reverse
import pytest


pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(user_factory):
    admin_user = user_factory(is_staff=True, is_superuser=True)
    client = Client()
    client.force_login(admin_user)
    return client


class TestUserAdmin:
    def test_users_listed(self, admin_client, user_factory):
        target = user_factory(
            email="listed@example.com",
            first_name="Listed",
            last_name="User",
        )

        response = admin_client.get(reverse("admin:users_user_changelist"))

        assert response.status_code == 200
        assert target.email.encode() in response.content
        assert target.first_name.encode() in response.content
        assert target.last_name.encode() in response.content

    def test_user_change_page_loads(self, admin_client, user_factory):
        target = user_factory()

        response = admin_client.get(
            reverse("admin:users_user_change", args=[target.id]),
        )

        assert response.status_code == 200

    def test_create_user_page_loads(self, admin_client):
        response = admin_client.get(reverse("admin:users_user_add"))

        assert response.status_code == 200

    def test_create_user_requires_first_and_last_name(self, admin_client):
        response = admin_client.post(
            reverse("admin:users_user_add"),
            {
                "email": "new@example.com",
                "password1": "Passwd123!",
                "password2": "Passwd123!",
            },
        )

        assert response.status_code == 200
        assert response.context["adminform"].form.errors.get("first_name")

    def test_deactivate_users_action(self, admin_client, user_factory):
        target = user_factory(is_active=True)

        admin_client.post(
            reverse("admin:users_user_changelist"),
            {
                "action": "deactivate_users",
                "_selected_action": [target.id],
            },
        )

        target.refresh_from_db()
        assert target.is_active is False

    def test_activate_users_action(self, admin_client, user_factory):
        target = user_factory(is_active=False)

        admin_client.post(
            reverse("admin:users_user_changelist"),
            {
                "action": "activate_users",
                "_selected_action": [target.id],
            },
        )

        target.refresh_from_db()
        assert target.is_active is True

    def test_requires_staff_login(self, user_factory):
        user_factory()  # a non-staff user exists, but we're not logged in as them
        anon_client = Client()

        response = anon_client.get(reverse("admin:users_user_changelist"))

        assert response.status_code == 302  # redirected to admin login
