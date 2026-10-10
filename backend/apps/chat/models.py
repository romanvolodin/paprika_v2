import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel
from apps.shots.models import Shot
from apps.versions.models import Version


def chat_attachment_upload_to(instance, filename: str) -> str:
    """Store every attachment under its own random directory.

    Same idea as `apps.versions.models.version_upload_to`: the original
    file name is kept, the random directory makes the URL unguessable
    (`/media/` is served without any authorization).
    """
    return f"chat/{uuid.uuid4().hex}/{filename}"


class Message(BaseModel):
    """
    A message in a shot's chat.

    Two kinds share the table (`type`):

    - `user` - written by a person: `text`, optional attachments, optional
      links to versions of the same shot, optional `reply_to` (a message
      of the same shot, checked by the API).
    - `system` - a record of something that happened on the shot (a
      version uploaded, a task added, a status or an assignee changed).
      Created by the API handlers that perform the action, in the same
      transaction. `event` says what happened and `payload` carries the
      details as they were at that moment (ids *and* names, so the line
      stays readable after the version or task is gone); the sentence
      itself is built by the client. System messages are never edited
      or deleted by users.

    Deleting a user message is soft: the row stays (with `text` wiped,
    `deleted_at` set, attachments and version links removed) so replies
    that quote it don't break. Deleted messages are left out of the chat
    list.

    `created_by` is the author (for system messages - the person who did
    the action).
    """

    class Type(models.TextChoices):
        USER = "user", _("user")
        SYSTEM = "system", _("system")

    class Event(models.TextChoices):
        VERSION_UPLOADED = "version_uploaded", _("version uploaded")
        TASK_ADDED = "task_added", _("task added")
        STATUS_CHANGED = "status_changed", _("status changed")
        ASSIGNEE_CHANGED = "assignee_changed", _("assignee changed")

    shot = models.ForeignKey(
        Shot,
        verbose_name=_("shot"),
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    type = models.CharField(
        _("type"), max_length=10, choices=Type.choices, default=Type.USER
    )
    text = models.TextField(_("text"), blank=True)
    event = models.CharField(
        _("event"),
        max_length=32,
        choices=Event.choices,
        blank=True,
        help_text=_("What happened. Only for system messages."),
    )
    payload = models.JSONField(
        _("payload"),
        default=dict,
        blank=True,
        help_text=_("Details of the event. Only for system messages."),
    )
    reply_to = models.ForeignKey(
        "self",
        verbose_name=_("reply to"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="replies",
    )
    versions = models.ManyToManyField(
        Version,
        verbose_name=_("versions"),
        blank=True,
        related_name="chat_messages",
    )
    edited_at = models.DateTimeField(_("edited at"), null=True, blank=True)
    deleted_at = models.DateTimeField(_("deleted at"), null=True, blank=True)

    class Meta:
        verbose_name = _("chat message")
        verbose_name_plural = _("chat messages")
        ordering = ["id"]
        indexes = [models.Index(fields=["shot", "id"], name="chat_msg_shot_id_idx")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(type="user", event="")
                | (models.Q(type="system") & ~models.Q(event="")),
                name="chat_message_event_only_for_system",
            )
        ]

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def mark_deleted(self, user) -> None:
        """Soft-delete: wipe the content, keep the row (see class docs)."""
        self.attachments.all().delete()
        self.reactions.all().delete()
        self.versions.clear()
        self.text = ""
        self.deleted_at = timezone.now()
        self.updated_by = user
        self.save(update_fields=["text", "deleted_at", "updated_by", "updated_at"])

    def __str__(self):
        return f"#{self.pk}"

    def __repr__(self):
        return f"<Message id={self.id} shot_id={self.shot_id} type={self.type}>"


class Attachment(BaseModel):
    """
    A file uploaded to a shot's chat.

    An independent resource: it is uploaded first and gets an id, and a
    message then refers to it by id. Until that happens (`message` is
    null) it belongs to nobody but its uploader (`created_by`), who can
    still remove it. Cleaning up attachments that never got attached is
    not implemented yet.
    """

    shot = models.ForeignKey(
        Shot,
        verbose_name=_("shot"),
        on_delete=models.CASCADE,
        related_name="chat_attachments",
    )
    message = models.ForeignKey(
        Message,
        verbose_name=_("message"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(_("file"), upload_to=chat_attachment_upload_to)
    filename = models.CharField(_("file name"), max_length=255)
    size = models.PositiveBigIntegerField(_("size"), help_text=_("In bytes."))
    content_type = models.CharField(_("content type"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("chat attachment")
        verbose_name_plural = _("chat attachments")
        ordering = ["id"]

    def __str__(self):
        return self.filename

    def __repr__(self):
        return f"<Attachment id={self.id} filename={self.filename}>"


class Reaction(BaseModel):
    """
    An emoji put on a message by a user (`created_by`).

    A user can put several different emoji on one message, but the same
    emoji only once. Removing a reaction deletes the row.
    """

    message = models.ForeignKey(
        Message,
        verbose_name=_("message"),
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    emoji = models.CharField(_("emoji"), max_length=64)

    class Meta:
        verbose_name = _("reaction")
        verbose_name_plural = _("reactions")
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["message", "created_by", "emoji"],
                name="unique_reaction_per_user_and_emoji",
            )
        ]

    def __str__(self):
        return self.emoji
