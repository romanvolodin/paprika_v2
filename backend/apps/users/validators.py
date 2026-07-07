from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


AVATAR_ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "gif"]
AVATAR_MAX_SIZE_MB = 2


def validate_avatar_size(file):
    if file.size > AVATAR_MAX_SIZE_MB * 1024 * 1024:
        raise ValidationError(
            _("Avatar file size must not exceed %(max_size)s MB.")
            % {"max_size": AVATAR_MAX_SIZE_MB}
        )
