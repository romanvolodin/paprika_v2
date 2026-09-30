from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


COVER_ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "gif"]
COVER_MAX_SIZE_MB = 5


def validate_cover_size(file):
    if file.size > COVER_MAX_SIZE_MB * 1024 * 1024:
        raise ValidationError(
            _("Cover file size must not exceed %(max_size)s MB.")
            % {"max_size": COVER_MAX_SIZE_MB}
        )
