# apps/courses/serializers/course.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.courses.models import Course

class CourseMinimalSerializer(serializers.ModelSerializer):
    level_display = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model  = Course
        fields = ["id", "name", "code", "level", "level_display"]


class CourseListSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name",         read_only=True)
    faculty_name    = serializers.CharField(source="department.faculty.name", read_only=True)
    level_display   = serializers.CharField(source="get_level_display",       read_only=True)
    subject_count   = serializers.IntegerField(source="subjects.count",       read_only=True)

    class Meta:
        model  = Course
        fields = [
            "id", "name", "code", "slug",
            "department_name", "faculty_name",
            "level", "level_display",
            "duration_months", "price",
            "subject_count", "is_active",
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    department    = serializers.SerializerMethodField() # MethodField ga o'zgartirildi
    level_display = serializers.CharField(source="get_level_display", read_only=True)
    subjects      = serializers.SerializerMethodField()
    total_credits = serializers.SerializerMethodField()

    class Meta:
        model  = Course
        fields = [
            "id", "name", "code", "slug", "department",
            "level", "level_display", "duration_months", "credit_hours",
            "description", "price", "subjects", "total_credits",
            "is_active", "created_at", "updated_at",
        ]

    def get_department(self, obj) -> dict:
        # Local import
        from apps.courses.serializers.department import DepartmentMinimalSerializer
        return DepartmentMinimalSerializer(obj.department).data

    def get_subjects(self, obj) -> list:
        from apps.courses.serializers.subject import SubjectListSerializer
        qs = obj.subjects.all().order_by("semester", "name")
        return SubjectListSerializer(qs, many=True).data

    def get_total_credits(self, obj) -> int:
        return sum(s.credit_hours for s in obj.subjects.all())


class CourseWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Course
        fields = [
            "department", "name", "code", "level",
            "duration_months", "credit_hours",
            "description", "price", "is_active",
        ]

    def validate_code(self, value: str) -> str:
        return value.upper().strip()

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError(_("Narx manfiy bo'lishi mumkin emas."))
        return value

    def validate_duration_months(self, value: int) -> int:
        if not (1 <= value <= 72):
            raise serializers.ValidationError(_("Davomiylik 1-72 oy orasida bo'lishi kerak."))
        return value