# apps/attendance/serializers.py
"""
Serializer — bu Django modeli ma'lumotlarini JSON formatiga
(yoki aksincha) o'girib beruvchi qatlam.

Bu faylda 2 ta serializer bor:
  1. AttendanceRecordSerializer  — talaba davomat yozuvi uchun
  2. AttendanceSessionSerializer — dars sessiyasi uchun (ichida record'lar ham bo'ladi)
"""

from rest_framework import serializers
from .models import AttendanceRecord, AttendanceSession


# ─────────────────────────────────────────────
# 1) AttendanceRecord Serializer
# ─────────────────────────────────────────────
class AttendanceRecordSerializer(serializers.ModelSerializer):
    """
    Bir talabaning davomat yozuvini (keldi/kelmadi/kech keldi/uzrli)
    JSON ko'rinishiga o'giradi.

    Qo'shimcha read-only maydonlar:
      - student_name  : talabaning to'liq ismi (bazadan o'qiladi, yozilmaydi)
      - status_display: statusning o'qilishi uchun matn ("Keldi", "Kelmadi"...)
    """

    # student.full_name maydonini to'g'ridan-to'g'ri chiqarish
    student_name = serializers.CharField(
        source="student.full_name",   # model ichidagi yo'l
        read_only=True,               # faqat o'qish, yozishda ishlatilmaydi
    )

    # get_status_display() — Django'ning choices matnini qaytaruvchi metodi
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model  = AttendanceRecord
        fields = [
            "id",
            "session",        # sessiya ID
            "student",        # talaba ID (yozishda kerak)
            "student_name",   # talaba ismi (faqat o'qish)
            "status",         # "present" | "absent" | "late" | "excused"
            "status_display", # "Keldi" | "Kelmadi" ...
            "minutes_late",   # kechikish daqiqasi (faqat status=late bo'lsa muhim)
            "note",           # qo'shimcha izoh
        ]
        # session va student faqat yozishda kerak, lekin read_only emas —
        # chunki talaba davomatini yaratayotganda ko'rsatamiz.
        extra_kwargs = {
            "session": {"write_only": True},  # JSON chiqishida ko'rinmaydi
        }

    def validate(self, attrs):
        """
        Maxsus tekshiruv:
        Agar status 'late' bo'lsa, minutes_late > 0 bo'lishi shart.
        """
        status      = attrs.get("status", AttendanceRecord.StatusChoices.PRESENT)
        minutes_late = attrs.get("minutes_late", 0)

        if status == AttendanceRecord.StatusChoices.LATE and minutes_late == 0:
            raise serializers.ValidationError(
                {"minutes_late": "Kech kelganda kechikish daqiqasini kiriting."}
            )
        return attrs


# ─────────────────────────────────────────────
# 2) AttendanceSession Serializer
# ─────────────────────────────────────────────
class AttendanceSessionSerializer(serializers.ModelSerializer):
    """
    Dars sessiyasini JSON ko'rinishiga o'giradi.
    Ichida o'sha sessiyadagi barcha talabalar davomat yozuvlari
    (records) ham nested holda chiqadi.
    """

    # Bu sessiyaga tegishli barcha AttendanceRecord'larni ichida ko'rsatamiz.
    # many=True — bir nechta record bo'lishi mumkin.
    # read_only=True — sessiya yaratayotganda record'larni bu yerda yubormaydi;
    #                   record'lar alohida endpoint orqali qo'shiladi.
    records = AttendanceRecordSerializer(many=True, read_only=True)

    # O'qituvchi ismini qulay ko'rish uchun
    teacher_name = serializers.CharField(
        source="teacher.full_name",
        read_only=True,
    )

    class Meta:
        model  = AttendanceSession
        fields = [
            "id",
            "schedule",      # jadval ID
            "group",         # guruh ID
            "subject",       # fan ID
            "teacher",       # o'qituvchi ID (yozishda kerak)
            "teacher_name",  # o'qituvchi ismi (faqat o'qish)
            "date",          # dars sanasi
            "start_time",    # boshlanish vaqti
            "end_time",      # tugash vaqti (bo'sh bo'lishi mumkin)
            "topic",         # dars mavzusi
            "notes",         # qo'shimcha izohlar
            "is_closed",     # dars yopilganmi?
            "records",       # nested — talabalar davomat yozuvlari
        ]
        # Ayrim maydonlarni faqat yaratishda kerak, chiqishda ko'rinmasin
        extra_kwargs = {
            "teacher": {"write_only": True},
            "schedule": {"write_only": True},
        }

    def validate(self, attrs):
        """
        Maxsus tekshiruv:
        end_time kiritilgan bo'lsa, u start_time'dan katta bo'lishi shart.
        """
        start = attrs.get("start_time")
        end   = attrs.get("end_time")

        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_time": "Tugash vaqti boshlanish vaqtidan katta bo'lishi kerak."}
            )
        return attrs


# ─────────────────────────────────────────────
# 3) Sessiyani yopish uchun alohida serializer
# ─────────────────────────────────────────────
class CloseSessionSerializer(serializers.Serializer):
    """
    Sessiyani yopish (close) action'i uchun kichik serializer.
    Faqat end_time qabul qiladi.
    """
    end_time = serializers.TimeField(
        help_text="Dars tugash vaqti, masalan: 14:30"
    )
    
    
    
    
    
