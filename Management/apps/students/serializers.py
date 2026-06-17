from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.students.models import StudentProfile
from apps.accounts.serializers.auth import UserMinimalSerializer

class StudentListSerializers(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id", "full_name", "email",
            "status", "status_display",
            "enrollment_date",
        ]

class StudentDetailSerializer(serializers.ModelSerializer):
    user           = UserMinimalSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)

    class Meta:
        model  = StudentProfile
        fields = [
            "id", "user",
            "date_of_birth", "gender", "gender_display",
            "address", "passport",
            "enrollment_date", "graduation_date",
            "status", "status_display",
            "created_at", "updated_at",
        ]

class StudentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model  = StudentProfile
        fields = [
            "user",                          
            "date_of_birth", "gender",
            "address", "passport",
            "enrollment_date", "graduation_date",
            "status",
        ]
    def validate_user(self, value):
        if StudentProfile.objects.filter(user=value).exists():
            raise serializers.ValidationError(
                _("Bu user uchun talaba profil allaqachon mavjud.")
            )
        return value
    
    def validate_enrollment_date(self, value):
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError(
                _("Qabul qilish sanasi bugungi kundan keyin bo'lishi mumkin emas.")
            )
        return value
    
class StudentUpdateSerializer(serializers.ModelSerializer):
    """Student o'z profilini tahrirlaydi"""

    class Meta:
        model  = StudentProfile
        fields = [
            "date_of_birth", "gender",   
            "address", "passport",
            "graduation_date", "status",
        ]

class StudentStatusSerializer(serializers.ModelSerializer):
    """Faqat status o'zgartirish — admin uchun"""

    class Meta:
        model  = StudentProfile
        fields = ["status"]

    def validate_status(self, value: str) -> str:
        allowed = StudentProfile.StatusChoices.values
        if value not in allowed:
            raise serializers.ValidationError(
                _("Ruxsat etilgan statuslar: %(statuses)s") % {
                    "statuses": ", ".join(allowed)
                }
            )
        return value