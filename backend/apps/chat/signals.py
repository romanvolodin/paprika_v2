from django.db.models.signals import post_delete
from django.dispatch import receiver

from apps.core.storage import delete_on_commit

from .models import Attachment


@receiver(post_delete, sender=Attachment)
def delete_attachment_file(sender, instance, **kwargs):
    """Remove a deleted attachment's file from storage.

    A signal rather than code in the endpoints because attachments also
    disappear via cascades (deleting a shot or a whole project) and when
    a message is deleted. Runs on commit so a rolled-back delete doesn't
    lose the file.
    """
    delete_on_commit(instance.file)
