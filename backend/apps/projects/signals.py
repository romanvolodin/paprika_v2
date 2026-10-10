from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.core.storage import delete_on_commit

from .models import Project


@receiver(post_delete, sender=Project)
def delete_project_cover(sender, instance, **kwargs):
    """Remove a deleted project's cover from storage.

    A signal rather than code in the delete endpoint because projects also
    disappear via cascades (deleting a whole company).
    """
    delete_on_commit(instance.cover)
