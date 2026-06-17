from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "created_by",
        "assigned_to",
        "priority",
        "status",
        "due_date",
        "completed_at",
    )
    list_filter = ("priority", "status", "due_date")
    search_fields = (
        "title",
        "description",
        "created_by__email",
        "assigned_to__email",
    )
    raw_id_fields = ("created_by", "assigned_to")
    date_hierarchy = "created_at"
    readonly_fields = ("completed_at",)
