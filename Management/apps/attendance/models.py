# apps/attendance/models.py
"""
Davomat modeli.
AttendanceSession: O'qituvchi darsni ochadi (real-time).
AttendanceRecord: Har bir talaba uchun alohida yozuv.
"""
 
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
 
 
class AttendanceSession(BaseModel):
    """
    Bir dars = bir session.
    O'qituvchi darsni boshlaganida session yaratiladi.
    """
    schedule = models.ForeignKey(
        "groups.Schedule",
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name=_("Jadval"),
    )
    group   = models.ForeignKey("groups.Group",   on_delete=models.CASCADE, related_name="sessions")
    subject = models.ForeignKey("courses.Subject", on_delete=models.CASCADE, related_name="sessions")
    teacher = models.ForeignKey(
        "teachers.TeacherProfile", on_delete=models.CASCADE, related_name="sessions"
    )
    date       = models.DateField(verbose_name=_("Dars sanasi"), db_index=True)
    start_time = models.TimeField(verbose_name=_("Boshlanish vaqti"))
    end_time   = models.TimeField(null=True, blank=True, verbose_name=_("Tugash vaqti"))
    topic      = models.CharField(max_length=255, blank=True, verbose_name=_("Dars mavzusi"))
    notes      = models.TextField(blank=True, verbose_name=_("Izohlar"))
    is_closed  = models.BooleanField(default=False, verbose_name=_("Yopilganmi"), db_index=True)
 
    class Meta:
        verbose_name        = _("Davomat sessiyasi")
        verbose_name_plural = _("Davomat sessiyalari")
        ordering            = ["-date", "-start_time"]
        indexes = [
            models.Index(fields=["group", "date"]),
            models.Index(fields=["teacher", "date"]),
            models.Index(fields=["subject", "date"]),
        ]
 
    def __str__(self):
        return f"{self.group.name} | {self.subject.name} | {self.date}"
 
 
class AttendanceRecord(BaseModel):
    """
    Har bir talaba uchun davomat yozuvi.
    """
 
    class StatusChoices(models.TextChoices):
        PRESENT = "present", _("Keldi")
        ABSENT  = "absent",  _("Kelmadi")
        LATE    = "late",    _("Kech keldi")
        EXCUSED = "excused", _("Uzrli sabab")
 
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="records",
        verbose_name=_("Sessiya"),
        db_index=True,
    )
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name=_("Talaba"),
        db_index=True,
    )
    status  = models.CharField(
        max_length=10, choices=StatusChoices.choices, default=StatusChoices.PRESENT,
        verbose_name=_("Holat"),
    )
    minutes_late = models.PositiveSmallIntegerField(
        default=0, verbose_name=_("Kechikish (daqiqa)")
    )
    note         = models.CharField(max_length=255, blank=True, verbose_name=_("Izoh"))
 
    class Meta:
        verbose_name        = _("Davomat yozuvi")
        verbose_name_plural = _("Davomat yozuvlari")
        unique_together     = [["session", "student"]]
        indexes = [
            models.Index(fields=["student", "status"]),
        ]
 
    def __str__(self):
        return f"{self.student.full_name} — {self.get_status_display()} | {self.session.date}"
 
 