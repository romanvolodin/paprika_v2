from django.contrib import admin

from .models import ShotTask, Task, TaskStatus, TaskType


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "abbreviation", "company")
    list_filter = ("company",)
    search_fields = ("name", "abbreviation")


@admin.register(TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "order", "is_default")
    list_filter = ("company",)
    search_fields = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "type", "project")
    list_filter = ("project", "type")
    search_fields = ("code", "name")
    readonly_fields = ("code",)


@admin.register(ShotTask)
class ShotTaskAdmin(admin.ModelAdmin):
    list_display = ("task", "shot", "status", "assignee")
    list_filter = ("status",)
    raw_id_fields = ("task", "shot", "assignee")
