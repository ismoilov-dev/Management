# apps/grades/serializers.py
"""
GRADES APP SERIALIZERS
======================

Bu faylda Grade va SemesterGPA modellar uchun serializer'lar yozilgan.
Serializer'lar Django REST Framework (DRF) asosida ishlaydi.

Asosiy vazifalar:
- Model ma'lumotlarini JSON formatga o'tkazish (serialize)
- Kiruvchi JSON ma'lumotlarni validatsiya qilish (deserialize)
- Foydalanuvchiga ko'rsatilmaydigan field'larni yashirish

Serializer'lar ro'yxati:
- GradeListSerializer     : Ro'yxat uchun (kam ma'lumot, tez ishlaydi)
- GradeDetailSerializer   : Batafsil ko'rish uchun
- GradeCreateSerializer   : Yangi baho qo'shish uchun
- GradeUpdateSerializer   : Bahoni tahrirlash uchun
- SemesterGPASerializer   : GPA ko'rish uchun
- StudentGPASummarySerializer: Talabaning umumiy GPA xulosasi
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Grade, SemesterGPA


# ============================================================
# GRADE SERIALIZERS
# ============================================================

class GradeListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name",read_only=True,)
    subject_name = serializers.CharField(source="subject.name",read_only=True,)
    teacher_name = serializers.CharField(source="teacher.full_name",read_only=True,)

    letter_grade = serializers.CharField(read_only=True)
    percentage   = serializers.FloatField(read_only=True)
    is_passed    = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Grade
        fields = ["id","student_name","subject_name","teacher_name","grade_type","score","percentage","letter_grade","is_passed","graded_at",]


class GradeDetailSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    student_id   = serializers.UUIDField(source="student.id", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    subject_id   = serializers.UUIDField(source="subject.id", read_only=True)
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    teacher_id   = serializers.UUIDField(source="teacher.id", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)
    group_id   = serializers.UUIDField(source="group.id", read_only=True)
    letter_grade = serializers.CharField(read_only=True)
    percentage   = serializers.FloatField(read_only=True)
    is_passed    = serializers.BooleanField(read_only=True)
    grade_type_display = serializers.CharField(source="get_grade_type_display",read_only=True,)

    class Meta:
        model  = Grade
        fields = ["id","student_id","student_name","subject_id","subject_name",
                  "teacher_id","teacher_name","group_id","group_name","grade_type",
                  "grade_type_display","score","max_score","percentage","letter_grade","is_passed",
                  "graded_at","comment","created_at","updated_at",]


class GradeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Grade
        fields = ["student","subject","teacher","group","grade_type","score","max_score","graded_at","comment",]

    def validate(self, attrs):
        score     = attrs.get("score", 0)
        max_score = attrs.get("max_score", 100)

        if score > max_score:
            raise serializers.ValidationError({
                "score": _(
                    f"Ball ({score}) maksimal balldan ({max_score}) katta bo'lishi mumkin emas."
                )
            })

        return attrs

    def validate_score(self, value):
        if value < 0:
            raise serializers.ValidationError(_("Ball manfiy bo'lishi mumkin emas."))
        return value

    def validate_max_score(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Maksimal ball 0 dan katta bo'lishi kerak."))
        return value

    def to_representation(self, instance):
        return GradeDetailSerializer(instance, context=self.context).data


class GradeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Grade
        fields = ["grade_type","score","max_score","graded_at","comment",]

    def validate(self, attrs):
        score     = attrs.get("score",     self.instance.score)
        max_score = attrs.get("max_score", self.instance.max_score)

        if score > max_score:
            raise serializers.ValidationError({
                "score": _(
                    f"Ball ({score}) maksimal balldan ({max_score}) katta bo'lishi mumkin emas."
                )
            })

        return attrs

    def to_representation(self, instance):
        return GradeDetailSerializer(instance, context=self.context).data


# ============================================================
# SEMESTER GPA SERIALIZERS
# ============================================================

class SemesterGPASerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    student_id   = serializers.UUIDField(source="student.id", read_only=True)
    credit_earned_percentage = serializers.FloatField(read_only=True)
    is_excellent_gpa         = serializers.BooleanField(read_only=True)
    is_passed_semester       = serializers.BooleanField(read_only=True)

    class Meta:
        model  = SemesterGPA
        fields = ["id","student_id","student_name","semester","year","gpa","total_credits",
                  "earned_credits","credit_earned_percentage","is_excellent_gpa","is_passed_semester","created_at","updated_at",]
        read_only_fields = fields 


class SemesterGPACreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SemesterGPA
        fields = ["student","semester","year","gpa","total_credits","earned_credits",]

    def validate_semester(self, value):
        if value not in [1, 2, 3]:
            raise serializers.ValidationError(_("Semestr 1, 2 yoki 3 bo'lishi kerak."))
        return value

    def validate_gpa(self, value):
        if not (0 <= value <= 4):
            raise serializers.ValidationError(_("GPA 0.0 dan 4.0 gacha bo'lishi kerak."))
        return value

    def validate(self, attrs):
        earned = attrs.get("earned_credits", 0)
        total  = attrs.get("total_credits",  0)

        if earned > total:
            raise serializers.ValidationError({
                "earned_credits": _(
                    f"Olingan kreditlar ({earned}) jami kreditdan ({total}) ko'p bo'lishi mumkin emas."
                )
            })

        return attrs

    def to_representation(self, instance):
        return SemesterGPASerializer(instance, context=self.context).data


class StudentGPASummarySerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    student_name = serializers.CharField()
    overall_gpa = serializers.DecimalField(max_digits=4, decimal_places=2)
    total_semesters = serializers.IntegerField()
    total_credits_attempted = serializers.IntegerField()
    total_credits_earned = serializers.IntegerField()
    semester_gpas = SemesterGPASerializer(many=True)
    grade_distribution = serializers.DictField(child=serializers.IntegerField())