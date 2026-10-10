from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.core.storage import delete_on_commit

from .models import User


@receiver(post_delete, sender=User)
def delete_user_avatar(sender, instance, **kwargs):
    """Remove a deleted user's avatar from storage."""
    delete_on_commit(instance.avatar)
