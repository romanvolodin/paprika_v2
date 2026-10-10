"""Where uploaded files live under `MEDIA_ROOT`, and how they are removed.

The full layout and the reasoning behind it are described in
`docs/src/dev/file_storage.md`. In short::

    users/<user_id>/avatar/<name>-<token>.<ext>
    <company_token>/.<company name>                          (marker file)
    <company_token>/<PROJECT>/<name>-<token>.<ext>           (project cover)
    <company_token>/<PROJECT>/shots/<SHOT>/versions/<VERSION>-<token>/<file>
    <company_token>/<PROJECT>/shots/<SHOT>/chat/<YYYY-MM-DD>/<name>-<token>.<ext>

Only things that never change end up in a path (project code, shot name,
version name, user id and the company's random `storage_token`), so a
stored file never has to move.

`/media/` is served without any authorization, so the random tokens are
what keeps files from being guessed: every uploaded object gets its own
(version folder, chat attachment, avatar, cover). The company token is not
a secret - it only hides the company's name from the URL.
"""

import datetime
import posixpath
import re
import secrets
import string
import unicodedata

from django.db import transaction


TOKEN_LENGTH = 8
_TOKEN_ALPHABET = string.ascii_lowercase + string.digits

MAX_SEGMENT_LENGTH = 80
MAX_FILENAME_LENGTH = 120
MAX_EXTENSION_LENGTH = 16

USERS_DIR = "users"

_UNSAFE = re.compile(r"[^\w.\-]+")


def make_token() -> str:
    """A fresh random token for a path (8 characters, `a-z0-9`)."""
    return "".join(secrets.choice(_TOKEN_ALPHABET) for _ in range(TOKEN_LENGTH))


def sanitize_name(
    value: str, *, max_length: int = MAX_SEGMENT_LENGTH, fallback: str = "_"
) -> str:
    """Turn arbitrary text into a safe single path segment.

    Letters (any alphabet), digits, `.`, `_` and `-` are kept; every run
    of other characters becomes one `_`. Leading dots are dropped (no
    hidden folders, no `.` / `..`), the result is cut to `max_length`
    and can't end with a dot (Windows doesn't allow it).

    Different inputs can end up with the same result (`A B` and `A_B`);
    that's accepted - see `docs/src/dev/file_storage.md`.
    """
    value = unicodedata.normalize("NFC", str(value))
    value = _UNSAFE.sub("_", value).lstrip(".")
    value = value[:max_length].rstrip(".")
    return value or fallback


def sanitize_filename(filename: str, *, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """Make an uploaded file's name safe while keeping it recognisable.

    The extension is kept as it was, only the part before it is cut if the
    whole name would be longer than `max_length`.
    """
    stem, extension = posixpath.splitext(_basename(filename))
    extension = _UNSAFE.sub("", extension)[:MAX_EXTENSION_LENGTH]
    if len(extension) < 2:
        extension = ""
    stem = sanitize_name(stem, max_length=max_length - len(extension), fallback="file")
    return stem + extension


def dir_with_token(name: str) -> str:
    """`<name>-<token>`: a readable folder name that can't be guessed."""
    return f"{sanitize_name(name)}-{make_token()}"


def file_with_token(filename: str) -> str:
    """`<name>-<token>.<ext>`: the uploaded file's name plus a random token."""
    stem, extension = posixpath.splitext(_basename(filename))
    extension = _UNSAFE.sub("", extension)[:MAX_EXTENSION_LENGTH]
    if len(extension) < 2:
        extension = ""
    stem = sanitize_name(stem, max_length=MAX_FILENAME_LENGTH - 20, fallback="file")
    return f"{stem}-{make_token()}{extension}"


def upload_date(now: datetime.datetime | None = None) -> str:
    """Folder name for chat uploads: today's date in UTC (`2026-10-08`)."""
    now = now or datetime.datetime.now(datetime.UTC)
    return now.astimezone(datetime.UTC).strftime("%Y-%m-%d")


# --- directories --------------------------------------------------------------


def company_dir(company) -> str:
    return company.storage_token


def project_dir(project) -> str:
    code = sanitize_name(project.code, max_length=50)
    return f"{company_dir(project.company)}/{code}"


def shot_dir(shot) -> str:
    return f"{project_dir(shot.project)}/shots/{sanitize_name(shot.name)}"


# --- deleting -----------------------------------------------------------------


def prune_empty_dirs(storage, directory: str) -> None:
    """Remove `directory` and its parents for as long as they are empty.

    Stops at the first folder that still holds something (for a company
    folder that's at the latest its marker file). A no-op on storages
    that have no real folders, such as object storage.
    """
    while directory:
        try:
            dirs, files = storage.listdir(directory)
        except FileNotFoundError, NotADirectoryError:
            # Already gone - check the parent.
            directory = posixpath.dirname(directory)
            continue
        if dirs or files:
            return
        try:
            storage.delete(directory)
        except OSError:
            return
        directory = posixpath.dirname(directory)


def delete_stored_file(storage, name: str) -> None:
    """Delete a stored file, then the folders it leaves empty."""
    storage.delete(name)
    prune_empty_dirs(storage, posixpath.dirname(name))


def delete_on_commit(*field_files) -> None:
    """Delete the given model files once the current transaction commits.

    Runs on commit so that a rolled-back delete doesn't lose the files.
    """
    items = [(f.storage, f.name) for f in field_files if f and f.name]
    if not items:
        return

    def _delete():
        for storage, name in items:
            delete_stored_file(storage, name)

    transaction.on_commit(_delete)


def _basename(filename: str) -> str:
    return posixpath.basename(str(filename).replace("\\", "/"))
