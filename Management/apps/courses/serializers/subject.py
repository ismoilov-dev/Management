# apps/courses/serializers/subject.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.courses.models import Subject

class SubjectMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Subject
        fields = ["id", "name", "code"]


class SubjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Subject
        fields = [
            "id", "name", "code",'slug',
            "semester", "credit_hours", "is_elective",
        ]


class SubjectDetailSerializer(serializers.ModelSerializer):
    course        = serializers.SerializerMethodField() 
    teachers      = serializers.SerializerMethodField()

    class Meta:
        model  = Subject
        fields = [
            "id", "name", "code", "slug",
            "course", "credit_hours", "semester",
            "description", "is_elective", "teachers",
            "created_at", "updated_at",
        ]

    def get_course(self, obj) -> dict:
        # Local import sirkulyar xatolikni oldini oladi
        from apps.courses.serializers.course import CourseMinimalSerializer
        return CourseMinimalSerializer(obj.course).data

    def get_teachers(self, obj) -> list:
        from apps.teachers.serializers import TeacherMinimalSerializer
        return TeacherMinimalSerializer(obj.teachers.all(), many=True).data


class SubjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Subject
        fields = [
            "course", "name", "code",
            "credit_hours", "semester",
            "description", "is_elective",
        ]

    def validate_code(self, value: str) -> str:
        return value.upper().strip()

    def validate_semester(self, value: int) -> int:
        if not (1 <= value <= 12):
            raise serializers.ValidationError(_("Semestr 1-12 orasida bo'lishi kerak."))
        return value

    def validate(self, attrs):
        course = attrs.get("course", getattr(self.instance, "course", None))
        code   = attrs.get("code",   getattr(self.instance, "code",   None))
        qs = Subject.objects.filter(course=course, code=code)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                _("Bu kursda bunday kodli fan allaqachon mavjud.")
            )
        return attrs