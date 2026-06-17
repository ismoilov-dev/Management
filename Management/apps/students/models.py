
from django.db import models
from django.utils.translation import gettext_lazy as _
 
from apps.core.models import BaseModel, GenderChoices
 
 
class StudentProfile(BaseModel):
    user          = models.OneToOneField("accounts.CustomUser", on_delete=models.CASCADE, related_name="student_profile")
    date_of_birth = models.DateField(null=True, blank=True)
    gender        = models.CharField(max_length=10, choices=GenderChoices.choices, blank=True)
    address       = models.TextField(blank=True)
    passport      = models.CharField(max_length=20, blank=True)
    enrollment_date = models.DateField()
    graduation_date = models.DateField(null=True, blank=True)

    class StatusChoices(models.TextChoices):
        ACTIVE    = "active",    _("Faol")
        GRADUATED = "graduated", _("Bitiruvchi")
        EXPELLED  = "expelled",  _("Chiqarib yuborilgan")
        SUSPENDED = "suspended", _("Akademik ta'tilda")

    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE, db_index=True)

    class Meta:
        verbose_name        = _("Talaba profili")
        verbose_name_plural = _("Talaba profillari")
        ordering            = ["user__last_name", "user__first_name"]

    def __str__(self):
        return self.user.full_name
 
class ParentStudentRelation(BaseModel):
    """
    Ota-ona va talaba o'rtasidagi bog'lanish.
    Bir ota-ona bir nechta talabaga ega bo'lishi mumkin.
    """
    parent = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="children",
        limit_choices_to={"role": "parent"},
        verbose_name=_("Ota-ona"),
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="parents",
        verbose_name=_("Talaba"),
    )
    relation = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Munosabat"),
        help_text=_("Masalan: Otasi, Onasi, Qo'riqchisi"),
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name=_("Asosiy aloqa shaxsimi"),
    )
 
    class Meta:
        verbose_name        = _("Ota-ona–Talaba bog'lanishi")
        verbose_name_plural = _("Ota-ona–Talaba bog'lanishlari")
        unique_together     = [["parent", "student"]]
 
    def __str__(self):
        return f"{self.parent.full_name} → {self.student.full_name}"
