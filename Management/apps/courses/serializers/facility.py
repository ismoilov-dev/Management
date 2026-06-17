from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.courses.models import Faculty, Department, Course, Subject, Room
# BU YERDAN DepartmentMinimalSerializer IMPORTI O'CHIRILDI!

class FacultyMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Faculty
        fields = ["id", "name", "code"]


class FacultyListSerializer(serializers.ModelSerializer):
    dean_name        = serializers.CharField(source="dean.user.full_name", read_only=True, default=None)
    department_count = serializers.IntegerField(source="departments.count", read_only=True)

    class Meta:
        model  = Faculty
        fields = ["id", "name", "code", "dean_name", "department_count", "is_active"]


class FacultyDetailSerializer(serializers.ModelSerializer):
    from apps.teachers.serializers import TeacherMinimalSerializer
    dean        = TeacherMinimalSerializer(read_only=True)
    departments = serializers.SerializerMethodField()

    class Meta:
        model  = Faculty
        fields = [
            "id", "name", "code", "slug",
            "description", "dean",
            "departments", "is_active",
            "created_at", "updated_at",
        ]

    def get_departments(self, obj):
        # Importni aynan shu yerga ko'chirdik (Lazy loading)
        from apps.courses.serializers.department import DepartmentMinimalSerializer
        
        qs = obj.departments.filter(is_active=True)
        return DepartmentMinimalSerializer(qs, many=True).data


class FacultyWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Faculty
        fields = ["name", "code", "description", "dean", "is_active"]

    def validate_code(self, value: str) -> str:
        return value.upper().strip()