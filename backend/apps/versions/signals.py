from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.core.storage import delete_on_commit

from .models import Version


@receiver(post_delete, sender=Version)
def delete_version_files(sender, instance, **kwargs):
    """Remove a deleted version's files from storage.

    A signal rather than code in the delete endpoint because versions
    also disappear via cascades (deleting a shot or a whole project),
    and those would otherwise leave orphaned files behind. Runs on
    commit so a rolled-back delete doesn't lose the files.
    """
    delete_on_commit(instance.source, instance.converted, instance.thumb)
