from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        email = "test@email.com"
        password = "Passwd123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        email = "test@EMAIL.com"
        user = get_user_model().objects.create_user(email, "Passwd123")

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, "Passwd123")

    def test_create_new_superuser(self):
        user = get_user_model().objects.create_superuser("test@email.com", "Passwd123")

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_user_without_password(self):
        user = get_user_model().objects.create_user(email="nopass@email.com")
        self.assertFalse(user.has_usable_password())

    def test_create_superuser_requires_password(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_superuser("admin@email.com", None)

    def test_create_superuser_is_staff_false_raises(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_superuser(
                "admin@email.com", "Passwd123", is_staff=False
            )

    def test_create_superuser_is_superuser_false_raises(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_superuser(
                "admin@email.com", "Passwd123", is_superuser=False
            )


class AdminSiteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            "admin@email.com", "Admin1234"
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email="user@email.com",
            password="User1234",
            first_name="Test_name",
            last_name="Test_lastname",
        )

    def test_users_listed(self):
        url = reverse("admin:users_user_changelist")
        response = self.client.get(url)

        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)

    def test_user_change_page(self):
        url = reverse("admin:users_user_change", args=[self.user.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_create_user_page(self):
        url = reverse("admin:users_user_add")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_create_user_page_requires_first_last_name(self):
        url = reverse("admin:users_user_add")
        response = self.client.post(
            url,
            {
                "email": "new@email.com",
                "password1": "Passwd123",
                "password2": "Passwd123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["adminform"], "first_name", "Обязательное поле."
        )


class AvatarValidationTests(TestCase):
    def test_avatar_too_large_raises(self):
        user = get_user_model()(email="bigavatar@email.com")
        big_file = SimpleUploadedFile(
            "avatar.png", b"0" * (3 * 1024 * 1024), content_type="image/png"
        )
        user.avatar = big_file

        with self.assertRaises(ValidationError):
            user.full_clean()
