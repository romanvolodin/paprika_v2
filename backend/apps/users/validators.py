from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_avatar_size(file):
    max_size_mb = 2
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(
            _("Avatar file size must not exceed %(max_size)s MB.")
            % {"max_size": max_size_mb}
        )
