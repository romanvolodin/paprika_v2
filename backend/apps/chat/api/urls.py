from dmr.routing import Router, path

from .views import (
    ChatAttachmentDetailController,
    ChatAttachmentUploadController,
    ChatListController,
    ChatMessageDetailController,
    ChatReactionController,
)


router = Router(
    "",
    [
        path(
            "shots/<int:shot_id>/chat/",
            ChatListController.as_view(),
            name="chat-list",
        ),
        path(
            "shots/<int:shot_id>/chat/attachments/",
            ChatAttachmentUploadController.as_view(),
            name="chat-attachment-upload",
        ),
        path(
            "chat/attachments/<int:attachment_id>/",
            ChatAttachmentDetailController.as_view(),
            name="chat-attachment-detail",
        ),
        path(
            "chat/<int:message_id>/",
            ChatMessageDetailController.as_view(),
            name="chat-message-detail",
        ),
        path(
            "chat/<int:message_id>/reactions/",
            ChatReactionController.as_view(),
            name="chat-message-reactions",
        ),
    ],
)
