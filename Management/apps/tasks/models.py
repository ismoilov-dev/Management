# apps/tasks/models.py
"""
Super Admin → Admin/Teacher ga vazifa berish.
"""
 
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
 
 
class Task(BaseModel):
    """Admin yoki Teacher uchun vazifa."""
 
    class Priority(models.TextChoices):
        LOW    = "low",    _("Past")
        MEDIUM = "medium", _("O'rta")
        HIGH   = "high",   _("Yuqori")
        URGENT = "urgent", _("Shoshilinch")
 
    class Status(models.TextChoices):
        TODO       = "todo",       _("Kutilmoqda")
        IN_PROGRESS= "in_progress",_("Jarayonda")
        DONE       = "done",       _("Bajarildi")
        CANCELLED  = "cancelled",  _("Bekor qilindi")
 
    created_by  = models.ForeignKey(
        "accounts.CustomUser", on_delete=models.CASCADE,
        related_name="created_tasks", verbose_name=_("Yaratuvchi"),
        limit_choices_to={"role__in": ["super_admin", "admin"]},
    )
    assigned_to = models.ForeignKey(
        "accounts.CustomUser", on_delete=models.CASCADE,
        related_name="assigned_tasks", verbose_name=_("Bajaruvchi"),
        limit_choices_to={"role__in": ["admin", "teacher"]},
    )
    title       = models.CharField(max_length=255, verbose_name=_("Sarlavha"))
    description = models.TextField(verbose_name=_("Tavsif"))
    priority    = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM, db_index=True
    )
    status      = models.CharField(
        max_length=15, choices=Status.choices, default=Status.TODO, db_index=True
    )
    due_date    = models.DateField(null=True, blank=True, verbose_name=_("Muddat"))
    completed_at = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        verbose_name        = _("Vazifa")
        verbose_name_plural = _("Vazifalar")
        ordering            = ["-created_at"]
        indexes = [
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["created_by", "status"]),
        ]
 
    def __str__(self):
        return f"{self.title} → {self.assigned_to.full_name} [{self.get_status_display()}]"
 