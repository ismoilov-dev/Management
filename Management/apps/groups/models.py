"""
Guruh va Dars jadvali modellari.
"""
 
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
 
 
class Group(BaseModel):
    """
    O'quv guruhi — kurs+o'qituvchi+xona+talabalar.
    """
    name   = models.CharField(max_length=100, verbose_name=_("Guruh nomi"))
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="groups",
        verbose_name=_("Kurs"),
        db_index=True,
    )
    teacher = models.ForeignKey(
        "teachers.TeacherProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="groups",
        verbose_name=_("Asosiy o'qituvchi"),
    )
    room = models.ForeignKey(
        "courses.Room",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="groups",
        verbose_name=_("Asosiy xona"),
    )
    students = models.ManyToManyField(
        "students.StudentProfile",
        through="GroupEnrollment",
        related_name="groups",
        verbose_name=_("Talabalar"),
    )
    start_date = models.DateField(verbose_name=_("Boshlanish sanasi"))
    end_date   = models.DateField(null=True, blank=True, verbose_name=_("Tugash sanasi"))
    max_students = models.PositiveSmallIntegerField(
        default=30, verbose_name=_("Maksimal talabalar soni")
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Faolmi"), db_index=True)
 
    class Meta:
        verbose_name        = _("Guruh")
        verbose_name_plural = _("Guruhlar")
        ordering            = ["-start_date", "name"]
        indexes = [
            models.Index(fields=["course", "is_active"]),
            models.Index(fields=["teacher", "is_active"]),
        ]
 
    def __str__(self):
        return f"{self.name} | {self.course.name}"
 
    @property
    def current_student_count(self):
        return self.enrollments.filter(is_active=True).count()
 
 
class GroupEnrollment(BaseModel):
    """
    Talabaning guruhga qo'shilishi (through model).
    Qo'shilish va chiqish tarixi saqlanadi.
    """
    group   = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(
        "students.StudentProfile", on_delete=models.CASCADE, related_name="enrollments"
    )
    enrolled_at = models.DateField(auto_now_add=True, verbose_name=_("Qo'shilgan sana"))
    left_at     = models.DateField(null=True, blank=True, verbose_name=_("Chiqgan sana"))
    is_active   = models.BooleanField(default=True, verbose_name=_("Faolmi"), db_index=True)
    notes       = models.TextField(blank=True, verbose_name=_("Izoh"))
 
    class Meta:
        verbose_name        = _("Guruh yozuvi")
        verbose_name_plural = _("Guruh yozuvlari")
        unique_together     = [["group", "student"]]
 
    def __str__(self):
        return f"{self.student.full_name} → {self.group.name}"
 
 
class Schedule(BaseModel):
    """
    Dars jadvali — guruh + fan + o'qituvchi + xona + vaqt.
    Har bir qator = bitta dars davri.
    """
 
    class DayChoices(models.IntegerChoices):
        MONDAY    = 1, _("Dushanba")
        TUESDAY   = 2, _("Seshanba")
        WEDNESDAY = 3, _("Chorshanba")
        THURSDAY  = 4, _("Payshanba")
        FRIDAY    = 5, _("Juma")
        SATURDAY  = 6, _("Shanba")
        SUNDAY    = 7, _("Yakshanba")
 
    group   = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="schedules")
    subject = models.ForeignKey("courses.Subject", on_delete=models.CASCADE, related_name="schedules")
    teacher = models.ForeignKey(
        "teachers.TeacherProfile", on_delete=models.CASCADE, related_name="schedules"
    )
    room       = models.ForeignKey("courses.Room", on_delete=models.CASCADE, related_name="schedules")
    day_of_week = models.SmallIntegerField(choices=DayChoices.choices, verbose_name=_("Hafta kuni"))
    start_time  = models.TimeField(verbose_name=_("Boshlanish vaqti"))
    end_time    = models.TimeField(verbose_name=_("Tugash vaqti"))
    valid_from  = models.DateField(verbose_name=_("Amal qilish boshlanishi"))
    valid_until = models.DateField(null=True, blank=True, verbose_name=_("Amal qilish tugashi"))
    is_active   = models.BooleanField(default=True)
 
    class Meta:
        verbose_name        = _("Dars jadvali")
        verbose_name_plural = _("Dars jadvallari")
        ordering            = ["day_of_week", "start_time"]
        indexes = [
            models.Index(fields=["group", "day_of_week"]),
            models.Index(fields=["teacher", "day_of_week"]),
            models.Index(fields=["room", "day_of_week", "start_time"]),
        ]
 
    def __str__(self):
        return (
            f"{self.group.name} | {self.subject.name} | "
            f"{self.get_day_of_week_display()} {self.start_time:%H:%M}"
        )
 