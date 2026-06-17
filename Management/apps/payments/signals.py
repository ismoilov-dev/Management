# apps/payments/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment  
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService


@receiver(post_save, sender=Payment)
def notify_payment(sender, instance, created, **kwargs):
    # Faqat to'lov muvaffaqiyatli bo'lganda
    if instance.is_paid and instance.status == "succeeded":
        # Bir marta yuborish uchun — oldin yuborilganmi tekshirish
        already_sent = Notification.objects.filter(
            recipient=instance.user,
            notif_type=Notification.NotifType.PAYMENT,
            metadata__payment_id=str(instance.payment_id),
        ).exists()

        if already_sent:
            return

        NotificationService.send(
            recipient=instance.user,
            title="To'lov muvaffaqiyatli",
            message=f"{instance.amount} {instance.currency.upper()} to'landi",
            notif_type=Notification.NotifType.PAYMENT,
            link=f"/payments/{instance.payment_id}/",
            metadata={
                "payment_id": str(instance.payment_id),
                "amount": str(instance.amount),
                "currency": instance.currency,
                "status": instance.status,
            },
        )