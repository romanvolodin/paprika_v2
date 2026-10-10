from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Attachment


@receiver(post_delete, sender=Attachment)
def delete_attachment_file(sender, instance, **kwargs):
    """Remove a deleted attachment's file from storage.

    A signal rather than code in the endpoints because attachments also
    disappear via cascades (deleting a shot or a whole project) and when
    a message is deleted. Runs on commit so a rolled-back delete doesn't
    lose the file.
    """
    field = instance.file
    if not (field and field.name):
        return
    storage, name = field.storage, field.name
    transaction.on_commit(lambda: storage.delete(name))
