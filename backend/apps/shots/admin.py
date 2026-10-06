from django.contrib import admin

from .models import Shot, ShotGroup


@admin.register(ShotGroup)
class ShotGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "project")
    list_filter = ("project",)


@admin.register(Shot)
class ShotAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "rec_timecode", "duration")
    list_filter = ("project",)
    filter_horizontal = ("groups",)
