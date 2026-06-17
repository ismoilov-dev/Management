from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel  # id, created_at, updated_at avtomatik qo'shiladi


class AssignmentModel(BaseModel):
    """
    O'qituvchi tomonidan berilgan uyga vazifa.
    Har bir assignment bitta teacher, subject va groupga tegishli.
    """

    title = models.CharField(
        max_length=255,
        verbose_name=_("Sarlavha"),
    )
    description = models.TextField(
        verbose_name=_("Topshiriq matni"),
    )
    teacher = models.ForeignKey(
        "teachers.TeacherProfile",
        on_delete=models.CASCADE,
        related_name="assignments",   # teacher.assignments.all() → o'sha teacherning barcha vazifalari
        verbose_name=_("O'qituvchi"),
    )
    subject = models.ForeignKey(
        "courses.Subject",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    group = models.ForeignKey(
        "groups.Group",
        on_delete=models.CASCADE,
        related_name="assignments",
        db_index=True,                # group bo'yicha tez qidiruv uchun index
    )
    due_date = models.DateTimeField(
        verbose_name=_("Topshirish muddati"),
        db_index=True,
    )
    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100,
        verbose_name=_("Maksimal ball"),
    )
    # null=True, blank=True → fayl majburiy emas
    attachment = models.FileField(
        upload_to="assignments/%Y/%m/",   # yuklangan fayl assignments/2025/01/ papkasiga boradi
        null=True,
        blank=True,
        verbose_name=_("Fayl"),
    )
    is_published = models.BooleanField(
        default=True,                     # yaratilganda darhol ko'rinadi
        verbose_name=_("E'lon qilinganmi"),
    )

    class Meta:
        verbose_name = _("Uyga vazifa")
        verbose_name_plural = _("Uyga vazifalar")
        ordering = ["-due_date"]          # eng yaqin deadline birinchi keladi
        indexes = [
            # group + due_date birga ishlatilganda tez qidiradi
            models.Index(fields=["group", "due_date"]),
            # teacher o'z published vazifalarini tez topadi
            models.Index(fields=["teacher", "is_published"]),
        ]

    def __str__(self):
        return f"{self.title} | {self.group.name} | {self.due_date:%Y-%m-%d}"


class SubmissionModel(BaseModel):
    """
    Talabaning uyga vazifaga javobi.
    Har bir (assignment + student) juftligi faqat bir marta topshira oladi.
    unique_together shu ishni bajaradi.
    """

    class StatusChoices(models.TextChoices):
        PENDING  = "pending",  _("Baholanmagan")   # yangi kelgan submission
        GRADED   = "graded",   _("Baholangan")      # teacher ball qo'ydi
        RETURNED = "returned", _("Qaytarilgan")     # teacher qayta ishlashni so'radi
        LATE     = "late",     _("Kech topshirilgan")  # deadline o'tib ketgan

    assignment = models.ForeignKey(
        AssignmentModel,
        on_delete=models.CASCADE,
        related_name="submissions",   # assignment.submissions.all() → barcha javoblar
        verbose_name=_("Vazifa"),
        db_index=True,
    )
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="submissions",   # student.submissions.all() → o'sha studentning javoblari
        verbose_name=_("Talaba"),
    )
    # blank=True → matn kiritish majburiy emas (fayl yuklash yetarli bo'lishi mumkin)
    content = models.TextField(
        blank=True,
        verbose_name=_("Javob matni"),
    )
    attachment = models.FileField(
        upload_to="submissions/%Y/%m/",
        null=True,
        blank=True,
        verbose_name=_("Fayl"),
    )
    # auto_now_add=True → faqat bir marta, yaratilgan vaqtda avtomatik yoziladi
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Topshirilgan vaqt"),
    )

    # --- Teacher tomonidan to'ldiriladi ---
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Ball"),
    )
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        db_index=True,
    )
    feedback = models.TextField(
        blank=True,
        verbose_name=_("O'qituvchi izohi"),
    )
    graded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Baholangan vaqt"),
    )

    class Meta:
        verbose_name = _("Topshiriq")
        verbose_name_plural = _("Topshiriqlar")
        # Bir student bitta assignmentga faqat bir marta javob bera oladi
        unique_together = [["assignment", "student"]]
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student.full_name} → {self.assignment.title}"

    @property
    def is_late(self):
        """Deadline o'tib ketgandan keyin topshirilganmi?"""
        return self.submitted_at > self.assignment.due_date