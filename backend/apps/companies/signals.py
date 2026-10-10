from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Company
from .storage import remove_marker, run_safely, sync_marker


@receiver(post_save, sender=Company)
def sync_company_marker(sender, instance, raw=False, **kwargs):
    """Create the company's marker file, or rename it after the company is.

    On commit, so a rolled-back save leaves nothing on disk.
    """
    if raw:
        return
    transaction.on_commit(lambda: run_safely(sync_marker, instance))


@receiver(post_delete, sender=Company)
def remove_company_marker(sender, instance, **kwargs):
    """Remove the marker (and the folder, if empty) of a deleted company.

    The company's files are removed by the signals of the models that own
    them (versions, chat attachments, covers), which run first because
    they are deleted along with the company.
    """
    transaction.on_commit(lambda: run_safely(remove_marker, instance))
