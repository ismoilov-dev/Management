from django.contrib import admin

from .models import Group, GroupEnrollment, Schedule


class GroupEnrollmentInline(admin.TabularInline):
    model = GroupEnrollment
    extra = 0
    raw_id_fields = ("student",)
    fields = ("student", "enrolled_at", "left_at", "is_active", "notes")
    readonly_fields = ("enrolled_at",)


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 0
    raw_id_fields = ("subject", "teacher", "room")
    fields = ("subject", "teacher", "room", "day_of_week", "start_time", "end_time", "is_active")


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "course",
        "teacher",
        "room",
        "start_date",
        "end_date",
        "max_students",
        "current_student_count",
        "is_active",
    )
    list_filter = ("is_active", "course", "start_date")
    search_fields = ("name", "course__name")
    raw_id_fields = ("course", "teacher", "room")
    inlines = [GroupEnrollmentInline, ScheduleInline]

    @admin.display(description="Talabalar soni")
    def current_student_count(self, obj):
        return obj.current_student_count


@admin.register(GroupEnrollment)
class GroupEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "group", "enrolled_at", "left_at", "is_active")
    list_filter = ("is_active", "enrolled_at")
    search_fields = ("student__user__first_name", "student__user__last_name", "group__name")
    raw_id_fields = ("group", "student")


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "group",
        "subject",
        "teacher",
        "room",
        "day_of_week",
        "start_time",
        "end_time",
        "is_active",
    )
    list_filter = ("day_of_week", "is_active", "group")
    search_fields = ("group__name", "subject__name")
    raw_id_fields = ("group", "subject", "teacher", "room")
