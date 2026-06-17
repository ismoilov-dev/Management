from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "payment_id",
        "payment_intent_id",   # pi_... shu yerda ko'rinadi
        "user",
        "amount",
        "currency",
        "status",
        "is_paid",
        "created_at",
    ]
    search_fields = ["payment_intent_id", "payment_id"]
    list_filter   = ["status", "is_paid", "currency"]