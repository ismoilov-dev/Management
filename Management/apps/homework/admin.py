from django.contrib import admin

from .models import AssignmentModel, SubmissionModel


class SubmissionInline(admin.TabularInline):
    model = SubmissionModel
    extra = 0
    raw_id_fields = ("student",)
    fields = ("student", "status", "score", "submitted_at", "graded_at")
    readonly_fields = ("submitted_at",)


@admin.register(AssignmentModel)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "teacher",
        "subject",
        "group",
        "due_date",
        "max_score",
        "is_published",
    )
    list_filter = ("is_published", "due_date", "subject", "group")
    search_fields = ("title", "description")
    raw_id_fields = ("teacher", "subject", "group")
    date_hierarchy = "due_date"
    inlines = [SubmissionInline]


@admin.register(SubmissionModel)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "assignment",
        "status",
        "score",
        "submitted_at",
        "graded_at",
    )
    list_filter = ("status", "submitted_at")
    search_fields = (
        "student__user__first_name",
        "student__user__last_name",
        "assignment__title",
    )
    raw_id_fields = ("assignment", "student")
    date_hierarchy = "submitted_at"
