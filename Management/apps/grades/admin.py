from django.contrib import admin

from .models import Grade, SemesterGPA


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "subject",
        "grade_type",
        "score",
        "max_score",
        "letter_grade",
        "teacher",
        "graded_at",
    )
    list_filter = ("grade_type", "graded_at", "subject", "group")
    search_fields = (
        "student__user__first_name",
        "student__user__last_name",
        "subject__name",
    )
    raw_id_fields = ("student", "subject", "teacher", "group")
    date_hierarchy = "graded_at"

    @admin.display(description="Harf baho")
    def letter_grade(self, obj):
        return obj.letter_grade


@admin.register(SemesterGPA)
class SemesterGPAAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "year",
        "semester",
        "gpa",
        "total_credits",
        "earned_credits",
    )
    list_filter = ("year", "semester")
    search_fields = (
        "student__user__first_name",
        "student__user__last_name",
    )
    raw_id_fields = ("student",)
    ordering = ("-year", "-semester")
