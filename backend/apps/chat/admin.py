from django.contrib import admin

from .models import Attachment, Message, Reaction


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "shot", "type", "event", "created_by", "created_at")
    list_filter = ("type", "event")
    raw_id_fields = ("shot", "reply_to", "versions")


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "filename", "shot", "message", "size", "created_at")
    raw_id_fields = ("shot", "message")


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "emoji", "created_by", "created_at")
    raw_id_fields = ("message",)
