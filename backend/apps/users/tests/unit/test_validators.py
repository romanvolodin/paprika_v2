from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from apps.users.validators import AVATAR_MAX_SIZE_MB, validate_avatar_size


pytestmark = pytest.mark.django_db


class TestValidateAvatarSize:
    def test_accepts_a_file_under_the_limit(self):
        small_file = SimpleUploadedFile(
            "avatar.png",
            b"0" * 1024,
            content_type="image/png",
        )

        validate_avatar_size(small_file)  # should not raise

    def test_rejects_a_file_over_the_limit(self):
        big_file = SimpleUploadedFile(
            "avatar.png",
            b"0" * (AVATAR_MAX_SIZE_MB * 1024 * 1024 + 1),
            content_type="image/png",
        )

        with pytest.raises(ValidationError):
            validate_avatar_size(big_file)

    def test_accepts_a_file_exactly_at_the_limit(self):
        exact_file = SimpleUploadedFile(
            "avatar.png",
            b"0" * (AVATAR_MAX_SIZE_MB * 1024 * 1024),
            content_type="image/png",
        )

        validate_avatar_size(exact_file)  # should not raise

    def test_full_clean_raises_for_oversized_avatar(self, user_factory):
        user = user_factory.build(email="bigavatar@example.com")
        big_file = SimpleUploadedFile(
            "avatar.png",
            b"0" * (AVATAR_MAX_SIZE_MB * 1024 * 1024 + 1),
            content_type="image/png",
        )
        user.avatar = big_file

        with pytest.raises(ValidationError):
            user.full_clean()
