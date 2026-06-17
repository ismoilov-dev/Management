# apps/notifications/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.grades.models import Grade  # o'zingizning modelingiz
from .models import Notification
from .services import NotificationService


@receiver(post_save, sender=Grade)
def notify_on_grade(sender, instance, created, **kwargs):
    if not created:
        return
    NotificationService.send(
        recipient=instance.student,
        sender=instance.teacher,
        title="Yangi baho qo'yildi",
        message=f"{instance.subject} — {instance.score} ball",
        notif_type=Notification.NotifType.GRADE,
        link=f"/grades/{instance.pk}/",
        metadata={"grade_id": instance.pk, "score": instance.score},
    )