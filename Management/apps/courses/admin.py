from django.contrib import admin

from .models import Faculty, Department, Course, Subject, Room


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "dean", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("dean",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "faculty", "head", "is_active")
    list_filter = ("is_active", "faculty")
    search_fields = ("name", "code")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("faculty", "head")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "department", "level", "duration_months", "price", "is_active")
    list_filter = ("level", "is_active", "department")
    search_fields = ("name", "code")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("department",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "course", "semester", "credit_hours", "is_elective")
    list_filter = ("is_elective", "semester", "course")
    search_fields = ("name", "code")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("course",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "building",
        "floor",
        "capacity",
        "room_type",
        "has_projector",
        "has_computer",
        "is_active",
    )
    list_filter = ("room_type", "is_active", "building", "has_projector", "has_computer")
    search_fields = ("name", "building")
