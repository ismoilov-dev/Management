from rest_framework import serializers
from .models import Payment


class CreatePaymentIntentSerializer(serializers.Serializer):
    """POST /api/payments/create-intent/"""
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="To'lov miqdori (masalan: 9.99)"
    )
    currency = serializers.CharField(
        max_length=10, default="usd",
        help_text="Valyuta kodi: usd, eur, uzs ..."
    )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value


class ConfirmPaymentSerializer(serializers.Serializer):
    """POST /api/payments/confirm/"""
    payment_id = serializers.UUIDField(
        help_text="create-intent dan kelgan payment_id (UUID)"
    )


class RefundSerializer(serializers.Serializer):
    """POST /api/payments/refund/"""
    payment_id = serializers.UUIDField(
        help_text="Bizning Payment UUID"
    )
    reason = serializers.ChoiceField(
        choices=["duplicate", "fraudulent", "requested_by_customer"],
        default="requested_by_customer",
        required=False
    )

class PaymentSerializer(serializers.ModelSerializer):
    """GET history & detail"""
    class Meta:
        model = Payment
        fields = [
            "payment_id", "amount", "currency",
            "status", "is_paid", "created_at",
        ]
        read_only_fields = fields