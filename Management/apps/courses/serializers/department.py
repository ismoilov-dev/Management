from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.courses.models import Faculty, Department, Course, Subject, Room
from apps.courses.serializers.facility import FacultyMinimalSerializer
# from apps.courses.serializers.course import CourseMinimalSerializer

class DepartmentMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Department
        fields = ["id", "name", "code"]


class DepartmentListSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source="faculty.name", read_only=True)
    head_name    = serializers.CharField(source="head.user.full_name", read_only=True, default=None)
    course_count = serializers.IntegerField(source="courses.count", read_only=True)

    class Meta:
        model  = Department
        fields = [
            "id", "name", "code",
            "faculty_name", "head_name",
            "course_count", "is_active",
        ]


class DepartmentDetailSerializer(serializers.ModelSerializer):
    faculty = FacultyMinimalSerializer(read_only=True)
    head    = serializers.SerializerMethodField()
    courses = serializers.SerializerMethodField()

    class Meta:
        model  = Department
        fields = [
            "id", "name", "code", "slug",
            "faculty", "head",
            "courses", "is_active",
            "created_at", "updated_at",
        ]

    def get_head(self, obj) -> dict | None:
        if obj.head:
            from apps.teachers.serializers import TeacherMinimalSerializer
            return TeacherMinimalSerializer(obj.head).data
        return None

    def get_courses(self, obj) -> list:
        from apps.courses.serializers.course import CourseMinimalSerializer
        qs = obj.courses.filter(is_active=True)
        return CourseMinimalSerializer(qs, many=True).data


class DepartmentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Department
        fields = ["faculty", "name", "code", "head", "is_active"]

    def validate_code(self, value: str) -> str:
        return value.upper().strip()

    def validate(self, attrs):
        faculty = attrs.get("faculty", getattr(self.instance, "faculty", None))
        name    = attrs.get("name",    getattr(self.instance, "name",    None))
        qs = Department.objects.filter(faculty=faculty, name=name)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                _("Bu fakultetda bunday nomli kafedra allaqachon mavjud.")
            )
        return attrs
