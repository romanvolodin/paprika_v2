from django.contrib import admin

from .models import Shot, ShotGroup, ShotStatus


@admin.register(ShotGroup)
class ShotGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "project")
    list_filter = ("project",)


@admin.register(ShotStatus)
class ShotStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "color", "order", "is_default")
    list_filter = ("company",)


@admin.register(Shot)
class ShotAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "status", "rec_timecode", "duration")
    list_filter = ("project", "status")
    filter_horizontal = ("groups",)
