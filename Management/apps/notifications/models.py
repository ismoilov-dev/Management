 
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel

class Notification(BaseModel):
    """In-app notification."""
 
    class NotifType(models.TextChoices):
        INFO    = "info",    _("Ma'lumot")
        SUCCESS = "success", _("Muvaffaqiyat")
        WARNING = "warning", _("Ogohlantirish")
        ERROR   = "error",   _("Xato")
        PAYMENT = "payment", _("To'lov")
        GRADE   = "grade",   _("Baho")
        ATTEND  = "attend",  _("Davomat")
        TASK    = "task",    _("Vazifa")
 
    recipient   = models.ForeignKey(
        "accounts.CustomUser", on_delete=models.CASCADE,
        related_name="notifications", db_index=True,
    )
    sender      = models.ForeignKey(
        "accounts.CustomUser", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="sent_notifications",
    )
    title       = models.CharField(max_length=255, verbose_name=_("Sarlavha"))
    message     = models.TextField(verbose_name=_("Xabar"))
    notif_type  = models.CharField(
        max_length=15, choices=NotifType.choices, default=NotifType.INFO
    )
    is_read     = models.BooleanField(default=False, db_index=True)
    read_at     = models.DateTimeField(null=True, blank=True)
    link        = models.CharField(max_length=500, blank=True, verbose_name=_("Havola"))
    # Generic FK o'rniga JSON — sodda va moslashuvchan
    metadata    = models.JSONField(default=dict, blank=True)
 
    class Meta:
        verbose_name        = _("Bildirishnoma")
        verbose_name_plural = _("Bildirishnomalar")
        ordering            = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "created_at"]),
        ]
 
    def __str__(self):
        return f"{self.recipient.full_name} | {self.title}"
 
 