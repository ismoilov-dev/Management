from django.contrib import admin

from .models import AttendanceSession, AttendanceRecord


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    raw_id_fields = ("student",)
    fields = ("student", "status", "minutes_late", "note")


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = (
        "group",
        "subject",
        "teacher",
        "date",
        "start_time",
        "end_time",
        "is_closed",
    )
    list_filter = ("is_closed", "date", "subject", "group")
    search_fields = ("group__name", "subject__name", "topic")
    date_hierarchy = "date"
    raw_id_fields = ("schedule", "group", "subject", "teacher")
    inlines = [AttendanceRecordInline]
    ordering = ("-date", "-start_time")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "status", "minutes_late")
    list_filter = ("status",)
    search_fields = ("student__user__first_name", "student__user__last_name")
    raw_id_fields = ("session", "student")
