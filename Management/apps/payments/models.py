from django.db import models
from django.contrib.auth import get_user_model
import uuid
from apps.core.models import BaseModel

User = get_user_model()

class Payment(BaseModel):
    class Status(models.TextChoices):
        PENDING   = "pending",   "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED    = "failed",    "Failed"
        REFUNDED  = "refunded",  "Refunded"

    user = models.ForeignKey(
        User, related_name="payments", null=True, blank=True,
        on_delete=models.SET_NULL          
    )
    payment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    payment_intent_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    currency    = models.CharField(max_length=10, default="usd")
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    is_paid     = models.BooleanField(default=False)   # backward compat uchun
    refund_id   = models.CharField(max_length=255, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.payment_id} — {self.amount} {self.currency} [{self.status}]"