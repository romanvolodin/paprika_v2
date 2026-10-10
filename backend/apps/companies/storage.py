"""The company's marker file in the media storage.

A company's folder is named by its random `storage_token`, so the name
can't be told from the folder. To keep the media tree understandable
without the database (say, when restoring from a backup), the folder holds
an empty file named after the company: `<token>/.<company name>`.

The marker is only a hint for people. The database is the source of truth,
so failures here are logged and never break the request.
"""

import logging

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from apps.core.storage import company_dir, prune_empty_dirs, sanitize_name


logger = logging.getLogger(__name__)


def marker_filename(company) -> str:
    # `sanitize_name` strips leading dots, so the one that makes the file
    # hidden is added afterwards.
    return "." + sanitize_name(company.name, fallback="company")


def _existing_markers(storage, directory: str) -> list[str]:
    try:
        _, files = storage.listdir(directory)
    except FileNotFoundError, NotADirectoryError:
        return []
    return [name for name in files if name.startswith(".")]


def sync_marker(company, storage=default_storage) -> None:
    """Make the company's folder hold exactly one marker, named after it now."""
    directory = company_dir(company)
    wanted = marker_filename(company)
    present = _existing_markers(storage, directory)

    for name in present:
        if name != wanted:
            storage.delete(f"{directory}/{name}")
    if wanted not in present:
        storage.save(f"{directory}/{wanted}", ContentFile(b""))


def remove_marker(company, storage=default_storage) -> None:
    """Delete the marker and, if nothing else is left, the folder."""
    directory = company_dir(company)
    for name in _existing_markers(storage, directory):
        storage.delete(f"{directory}/{name}")
    prune_empty_dirs(storage, directory)


def run_safely(function, company) -> None:
    try:
        function(company)
    except Exception:
        logger.exception("Could not update the media marker of company %s", company.pk)
