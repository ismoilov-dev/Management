from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel, GenderChoices


class TeacherProfile(BaseModel):

    user = models.OneToOneField(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        verbose_name=_("Foydalanuvchi"),
    )

    # Shaxsiy
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_("Tug'ilgan sana"))
    gender        = models.CharField(max_length=10, choices=GenderChoices.choices, blank=True, verbose_name=_("Jins"))
    bio           = models.TextField(blank=True, verbose_name=_("Biografiya"))
    linkedin      = models.URLField(blank=True, verbose_name=_("LinkedIn"))

    # Akademik
    specialization   = models.CharField(max_length=255, blank=True, verbose_name=_("Mutaxassislik"))
    degree           = models.CharField(max_length=100, blank=True, verbose_name=_("Ilmiy daraja"))
    hire_date        = models.DateField(null=True, blank=True, verbose_name=_("Ishga kirgan sana"))
    max_weekly_hours = models.PositiveSmallIntegerField(default=40, verbose_name=_("Haftalik max soatlar"))

    subjects = models.ManyToManyField(
        "courses.Subject",
        blank=True,
        related_name="teachers",
        verbose_name=_("Fanlar"),
    )

    class StatusChoices(models.TextChoices):
        ACTIVE   = "active",   _("Faol")
        ON_LEAVE = "on_leave", _("Ta'tilda")
        INACTIVE = "inactive", _("Faolsiz")

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        db_index=True,
        verbose_name=_("Holat"),
    )

    class Meta:
        verbose_name        = _("O'qituvchi profili")
        verbose_name_plural = _("O'qituvchi profillari")
        ordering            = ["user__last_name", "user__first_name"]

    def __str__(self):
        return self.user.full_name