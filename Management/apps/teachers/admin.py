from django.contrib import admin

from .models import TeacherProfile


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "specialization",
        "degree",
        "status",
        "hire_date",
        "max_weekly_hours",
    )
    list_filter = ("status", "gender", "hire_date")
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "specialization",
        "degree",
    )
    raw_id_fields = ("user",)
    filter_horizontal = ("subjects",)
