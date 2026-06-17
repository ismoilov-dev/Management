# apps/teachers/serializers.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.teachers.models import TeacherProfile
from apps.accounts.serializers.auth import UserMinimalSerializer



def get_subject_queryset():
    from apps.courses.models import Subject
    return Subject.objects.all()



class TeacherMinimalSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ["id", "full_name"]



class TeacherListSerializer(serializers.ModelSerializer):
    full_name      = serializers.CharField(source="user.full_name", read_only=True)
    email          = serializers.EmailField(source="user.email",    read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = TeacherProfile
        fields = [
            "id", "full_name", "email",
            "specialization", "status", "status_display", "hire_date",
        ]



class TeacherDetailSerializer(serializers.ModelSerializer):
    user                = UserMinimalSerializer(read_only=True)
    status_display      = serializers.CharField(source="get_status_display", read_only=True)
    gender_display      = serializers.CharField(source="get_gender_display", read_only=True)
    years_of_experience = serializers.SerializerMethodField()
    subjects            = serializers.SerializerMethodField()

    class Meta:
        model = TeacherProfile
        fields = [
            "id", "user",
            "date_of_birth", "gender", "gender_display",
            "bio", "linkedin",
            "specialization", "degree",
            "hire_date", "years_of_experience", "max_weekly_hours",
            "subjects", "status", "status_display",
            "created_at", "updated_at",
        ]

    def get_years_of_experience(self, obj) -> int:
        from datetime import date
        if obj.hire_date:
            return (date.today() - obj.hire_date).days // 365
        return 0

    def get_subjects(self, obj) -> list:
        from apps.courses.serializers.subject import SubjectListSerializer
        return SubjectListSerializer(obj.subjects.all(), many=True).data



class TeacherUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TeacherProfile
        fields = [
            'user',
            "date_of_birth", "gender", "bio", "linkedin",
            "specialization", "degree",
            "max_weekly_hours", "status",
        ]

    def get_fields(self):
        from apps.courses.models import Subject  # lazyy impor
        fields = super().get_fields()

        # Bu yerda to'liq field yaratamiz
        fields["subject_ids"] = serializers.PrimaryKeyRelatedField(
            many=True,
            write_only=True,
            required=False,
            source="subjects",
            queryset=Subject.objects.all(),  
        )
        return fields

    def validate_max_weekly_hours(self, value: int) -> int:
        if not (1 <= value <= 80):
            raise serializers.ValidationError(
                _("Haftalik soatlar 1 va 80 orasida bo'lishi kerak.")
            )
        return value

    def update(self, instance, validated_data):
        subjects = validated_data.pop("subjects", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if subjects is not None:
            instance.subjects.set(subjects)

        return instance



class TeacherStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ["status"]

    def validate_status(self, value: str) -> str:
        allowed = TeacherProfile.StatusChoices.values
        if value not in allowed:
            raise serializers.ValidationError(
                _("Ruxsat etilgan statuslar: %(statuses)s") % {
                    "statuses": ", ".join(allowed)
                }
            )
        return value

class TeacherCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model  = TeacherProfile
        fields = [
            "user",              
            "date_of_birth", "gender", "bio", "linkedin",
            "specialization", "degree",
            "hire_date", "max_weekly_hours",
            # "subject_ids",
            "status",
        ]

    def get_fields(self):
        from apps.courses.models import Subject
        fields = super().get_fields()
        fields["subject_ids"] = serializers.SlugRelatedField(
            many=True,
            write_only=True,
            required=False,
            source="subjects",
            slug_field="slug",
            queryset=Subject.objects.all(),
        )
        return fields

    def validate_user(self, value):
        # Teacher profil allaqachon bor-yo'qligini tekshirish
        if TeacherProfile.objects.filter(user=value).exists():
            raise serializers.ValidationError(
                _("Bu user uchun teacher profil allaqachon mavjud.")
            )
        return value

    def validate_hire_date(self, value):
        from datetime import date
        if value and value > date.today():
            raise serializers.ValidationError(
                _("Ishga kirgan sana kelajakda bo'lishi mumkin emas.")
            )
        return value

    def validate_max_weekly_hours(self, value: int) -> int:
        if not (1 <= value <= 80):
            raise serializers.ValidationError(
                _("Haftalik soatlar 1 va 80 orasida bo'lishi kerak.")
            )
        return value

    def create(self, validated_data):
        subjects = validated_data.pop("subjects", [])
        profile  = TeacherProfile.objects.create(**validated_data)
        if subjects:
            profile.subjects.set(subjects)
        return profile