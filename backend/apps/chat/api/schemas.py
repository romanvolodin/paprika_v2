import datetime as dt

import pydantic

from apps.users.api.schemas import UserOut
from apps.versions.api.schemas import VersionOut


class ShotChatPath(pydantic.BaseModel):
    shot_id: int


class MessagePath(pydantic.BaseModel):
    message_id: int


class AttachmentPath(pydantic.BaseModel):
    attachment_id: int


class ChatListQuery(pydantic.BaseModel):
    """Cursor pagination params for `GET /api/v1/shots/<id>/chat/`."""

    limit: int = pydantic.Field(
        default=50,
        ge=1,
        le=100,
        description="How many messages to return.",
    )
    before: int | None = pydantic.Field(
        default=None,
        description="Return the `limit` messages older than the message "
        "with this id (to load earlier history).",
    )
    around: int | None = pydantic.Field(
        default=None,
        description="Return a window of at most `limit` messages around "
        "the message with this id, including it (to jump to a quoted "
        "message). Can't be combined with `before`.",
    )


class ChatAttachmentFileMetadata(pydantic.BaseModel):
    """Validates the uploaded file's metadata.

    The size limit is configurable (`PAPRIKA_CHAT_ATTACHMENT_MAX_FILE_SIZE_MB`)
    and is enforced in the view so it can answer 413.
    """

    name: str = pydantic.Field(min_length=1, max_length=255)
    size: int


class ChatAttachmentFiles(pydantic.BaseModel):
    """Files accepted by `POST /api/v1/shots/<shot_id>/chat/attachments/`."""

    file: ChatAttachmentFileMetadata


class AttachmentOut(pydantic.BaseModel):
    """A file attached to a chat message (or uploaded and not sent yet)."""

    id: int
    url: str = pydantic.Field(description="Absolute URL of the file.")
    filename: str
    size: int = pydantic.Field(description="In bytes.")
    content_type: str


class ReactionSummaryOut(pydantic.BaseModel):
    """One emoji on a message, collapsed over everybody who put it.

    There is no counter on purpose: it is the length of `user_ids`.
    """

    emoji: str
    user_ids: list[int] = pydantic.Field(
        description="Who put the emoji, in the order they did it."
    )


class ReactionsOut(pydantic.BaseModel):
    """All reactions of a message, in the order they first appeared."""

    reactions: list[ReactionSummaryOut]


class ReactionIn(pydantic.BaseModel):
    emoji: str = pydantic.Field(
        min_length=1,
        max_length=64,
        pattern=r"^\S+$",
        description="Any emoji, no spaces.",
    )


class ReactionQuery(pydantic.BaseModel):
    """Query params of `DELETE /api/v1/chat/<id>/reactions/`."""

    emoji: str = pydantic.Field(
        min_length=1,
        max_length=64,
        pattern=r"^\S+$",
        description="The emoji to remove.",
    )


class ReplyToOut(pydantic.BaseModel):
    """The message a message replies to, as a short quote."""

    id: int
    author: UserOut | None
    text: str = pydantic.Field(
        description="The first 200 characters of the quoted text. Empty if "
        "the quoted message was deleted."
    )
    deleted: bool


class MessageOut(pydantic.BaseModel):
    """Public representation of a chat message."""

    id: int
    shot_id: int
    type: str = pydantic.Field(description="`user` or `system`.")
    text: str = pydantic.Field(description="Empty for system messages.")
    event: str | None = pydantic.Field(
        description="`version_uploaded`, `task_added`, `status_changed` or "
        "`assignee_changed` for system messages, null for user messages."
    )
    payload: dict = pydantic.Field(
        description="Details of the event as they were when it happened "
        "(ids and names); empty for user messages."
    )
    reply_to: ReplyToOut | None
    versions: list[VersionOut] = pydantic.Field(
        description="Versions of the shot the message refers to."
    )
    attachments: list[AttachmentOut]
    reactions: list[ReactionSummaryOut]
    edited_at: dt.datetime | None = pydantic.Field(
        description="Set when the text was edited, null otherwise."
    )
    created_by: UserOut | None = pydantic.Field(
        description="The author (for a system message - the person who did "
        "the action), or null if that user has since been deleted."
    )
    created_at: dt.datetime
    updated_at: dt.datetime


class ChatListOut(pydantic.BaseModel):
    items: list[MessageOut] = pydantic.Field(
        description="In chronological order (oldest first)."
    )
    has_older: bool = pydantic.Field(description="There are older messages.")
    has_newer: bool = pydantic.Field(description="There are newer messages.")


class MessageCreateIn(pydantic.BaseModel):
    text: str = pydantic.Field(
        default="",
        description="Surrounding whitespace is trimmed. The length limit is "
        "configurable (`PAPRIKA_CHAT_MESSAGE_MAX_LENGTH`, 2000 by default).",
    )
    reply_to_id: int | None = pydantic.Field(
        default=None,
        description="A user message of the same shot to reply to.",
    )
    version_ids: list[int] = pydantic.Field(
        default_factory=list,
        description="Versions of the same shot the message refers to.",
    )
    attachment_ids: list[int] = pydantic.Field(
        default_factory=list,
        description="Ids of files uploaded earlier by the same user.",
    )


class MessageUpdateIn(pydantic.BaseModel):
    text: str
