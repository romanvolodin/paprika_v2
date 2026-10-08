from django.contrib import admin

from .models import Version


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ("name", "shot", "project", "type", "created_at")
    list_filter = ("project", "type")
    search_fields = ("name",)
    raw_id_fields = ("shot",)
