from django.contrib import admin

from .models import StudentProfile, ParentStudentRelation


class ParentStudentRelationInline(admin.TabularInline):
    model = ParentStudentRelation
    extra = 0
    raw_id_fields = ("parent",)
    fields = ("parent", "relation", "is_primary")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "status",
        "gender",
        "enrollment_date",
        "graduation_date",
    )
    list_filter = ("status", "gender", "enrollment_date")
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "passport",
    )
    raw_id_fields = ("user",)
    inlines = [ParentStudentRelationInline]


@admin.register(ParentStudentRelation)
class ParentStudentRelationAdmin(admin.ModelAdmin):
    list_display = ("parent", "student", "relation", "is_primary")
    list_filter = ("is_primary",)
    search_fields = (
        "parent__first_name",
        "parent__last_name",
        "student__user__first_name",
        "student__user__last_name",
    )
    raw_id_fields = ("parent", "student")
