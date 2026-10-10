import posixpath

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.core.storage import dir_with_token, sanitize_filename, shot_dir
from apps.projects.models import Project
from apps.shots.models import Shot


def version_upload_to(instance, filename: str) -> str:
    """Where the uploaded `source` file goes.

    `<company token>/<PROJECT>/shots/<SHOT>/versions/<VERSION>-<token>/<file>`.

    The original file name is kept (people download originals and expect
    to recognise them), while the random token in the folder name makes
    the URL unguessable - `/media/` is served by Caddy without any
    authorization, so the path itself is the only thing keeping other
    people's versions private.
    """
    version_dir = f"{shot_dir(instance.shot)}/versions/{dir_with_token(instance.name)}"
    return f"{version_dir}/{sanitize_filename(filename)}"


def version_derived_upload_to(instance, filename: str) -> str:
    """Where files made from the source (`converted`, `thumb`) go.

    Right next to the source, so a version is one self-contained folder.
    Name them after the source file, e.g. `PRJ_0010_v01.mov_thumb.jpg`, so
    it's clear what each was made from.

    Relies on `source` being saved before the fields below it (Django
    saves file fields in the order they are declared on the model).
    """
    version_dir = posixpath.dirname(instance.source.name) if instance.source else ""
    if not version_dir:
        # The source isn't stored yet - give the files a folder of their own.
        version_dir = (
            f"{shot_dir(instance.shot)}/versions/{dir_with_token(instance.name)}"
        )
    return f"{version_dir}/{sanitize_filename(filename)}"


class Version(BaseModel):
    """One uploaded result of work on a shot - a video or a still image.

    Attaches directly to `Shot` (not to a task): a single version may
    address several tasks at once.

    `name` is taken from the uploaded file's name without its extension
    (`PRJ_0060_v01.mp4` -> `PRJ_0060_v01`) and is unique within the
    project. There is deliberately no auto-incremented number - versions
    may skip numbers (v01, then v04) and be uploaded out of order. A
    version can't be renamed or edited once uploaded: delete it and
    upload again.

    `project` duplicates `shot.project` so the "unique name per project"
    rule can be a real database constraint. It's filled in automatically
    from the shot on first save.

    Files:
    - `source` - the original upload (mp4/jpg/png).
    - `converted` - browser-friendly rendition. Empty until a conversion
      step exists; clients should play `converted` and fall back to
      `source`.
    - `thumb` - small JPG for lists and cards (for videos: a single
      frame, see `settings.VERSION_THUMB_FRAME_POSITION`).

    Video-only fields (`duration`, `fps`, `codec`) are empty for images.
    """

    class Type(models.TextChoices):
        VIDEO = "video", _("Video")
        IMAGE = "image", _("Image")

    project = models.ForeignKey(
        Project,
        verbose_name=_("project"),
        on_delete=models.CASCADE,
        related_name="versions",
        editable=False,
    )
    shot = models.ForeignKey(
        Shot,
        verbose_name=_("shot"),
        on_delete=models.CASCADE,
        related_name="versions",
    )
    name = models.CharField(_("name"), max_length=255)
    type = models.CharField(_("type"), max_length=10, choices=Type.choices)

    source = models.FileField(
        _("source file"), upload_to=version_upload_to, max_length=512
    )
    converted = models.FileField(
        _("converted file"),
        upload_to=version_derived_upload_to,
        blank=True,
        max_length=512,
    )
    thumb = models.FileField(
        _("thumbnail"), upload_to=version_derived_upload_to, blank=True, max_length=512
    )

    width = models.PositiveIntegerField(_("width"), help_text=_("In pixels."))
    height = models.PositiveIntegerField(_("height"), help_text=_("In pixels."))
    duration = models.PositiveIntegerField(
        _("duration"),
        null=True,
        blank=True,
        help_text=_("Length in frames. Empty for images."),
    )
    fps = models.FloatField(
        _("frame rate"),
        null=True,
        blank=True,
        help_text=_("Frames per second. Empty for images."),
    )
    codec = models.CharField(
        _("codec"),
        max_length=32,
        blank=True,
        help_text=_("Video codec name, e.g. h264. Empty for images."),
    )
    file_size = models.PositiveBigIntegerField(
        _("file size"), help_text=_("Size of the source file, in bytes.")
    )

    class Meta:
        verbose_name = _("version")
        verbose_name_plural = _("versions")
        # Newest first - the latest upload is what people look at.
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"], name="unique_version_name_per_project"
            )
        ]

    def save(self, *args, **kwargs):
        if not self.project_id and self.shot_id:
            self.project_id = self.shot.project_id
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Version id={self.id} name={self.name} shot_id={self.shot_id}>"
