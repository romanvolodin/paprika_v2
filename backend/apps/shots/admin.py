from django.contrib import admin

from .models import ShotGroup


@admin.register(ShotGroup)
class ShotGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "project")
    list_filter = ("project",)
