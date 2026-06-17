import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
from .models import Payment
from .serializers import (
    CreatePaymentIntentSerializer,
    ConfirmPaymentSerializer,
    RefundSerializer,
    PaymentSerializer,
)

stripe.api_key = settings.STRIPE_SECRET_KEY


# ──────────────────────────────────────────────
# POST /api/payments/create-intent/
# ──────────────────────────────────────────────
# apps/payments/views.py

class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="To'lov niyati yaratish",
        request=CreatePaymentIntentSerializer,
        responses={
            200: OpenApiResponse(description="client_secret va payment_id qaytaradi"),
            400: OpenApiResponse(description="Validation xatosi"),
        },
        tags=["Payments"],
    )
    def post(self, request):
        serializer = CreatePaymentIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount   = serializer.validated_data["amount"]
        currency = serializer.validated_data["currency"]

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency=currency,
                metadata={"user_id": str(request.user.pk)},
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never",
                },
                payment_method="pm_card_visa",
                confirm=True,
            )

            payment = Payment.objects.create(
                user=request.user,
                amount=amount,
                currency=currency,
                payment_intent_id=intent.id,
                status=Payment.Status.SUCCEEDED if intent.status == "succeeded" else Payment.Status.PENDING,
                is_paid=intent.status == "succeeded",
            )

            # ── Notification ──────────────────────────────
            if payment.is_paid:
                NotificationService.send(
                    recipient=request.user,
                    title="To'lov muvaffaqiyatli amalga oshdi",
                    message=f"{amount} {currency.upper()} miqdoridagi to'lov qabul qilindi.",
                    notif_type=Notification.NotifType.PAYMENT,
                    link=f"/payments/{payment.payment_id}/",
                    metadata={
                        "payment_id": str(payment.payment_id),
                        "amount":     str(amount),
                        "currency":   currency,
                        "status":     payment.status,
                    },
                )
            # ─────────────────────────────────────────────

            return Response({
                "payment_id":    str(payment.payment_id),
                "client_secret": intent.client_secret,
                "amount":        str(amount),
                "currency":      currency,
                "status":        payment.status,
                "is_paid":       payment.is_paid,
            }, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# POST /api/payments/confirm/
# ──────────────────────────────────────────────
class ConfirmPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="To'lov holatini tasdiqlash",
        request=ConfirmPaymentSerializer,
        responses={
            200: PaymentSerializer,
            404: OpenApiResponse(description="Payment topilmadi"),
            400: OpenApiResponse(description="Stripe xatosi"),
        },
        tags=["Payments"],
    )
    def post(self, request):
        serializer = ConfirmPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ✅ payment_id (UUID) bilan DB dan topamiz
        try:
            payment = Payment.objects.get(
                payment_id=serializer.validated_data["payment_id"],
                user=request.user,
            )
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not payment.payment_intent_id:
            return Response(
                {"error": "PaymentIntent ID missing."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Stripe dan haqiqiy statusni olamiz
        try:
            intent = stripe.PaymentIntent.retrieve(payment.payment_intent_id)
        except stripe.error.InvalidRequestError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Status yangilash
        status_map = {
            "succeeded":               Payment.Status.SUCCEEDED,
            "requires_payment_method": Payment.Status.FAILED,
            "canceled":                Payment.Status.FAILED,
            "processing":              Payment.Status.PENDING,
        }
        payment.status  = status_map.get(intent.status, Payment.Status.PENDING)
        payment.is_paid = (intent.status == "succeeded")
        payment.save()

        return Response({
            **PaymentSerializer(payment).data,
            "stripe_status": intent.status,
        }, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────
# POST /api/payments/refund/
# ──────────────────────────────────────────────
class RefundPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="To'lovni qaytarish (refund)",
        request=RefundSerializer,
        responses={
            200: OpenApiResponse(description="Refund muvaffaqiyatli"),
            400: OpenApiResponse(description="To'lov to'lanmagan yoki xato"),
            404: OpenApiResponse(description="Payment topilmadi"),
        },
        tags=["Payments"],
    )
    def post(self, request):
        serializer = RefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment = Payment.objects.get(
                payment_id=serializer.validated_data["payment_id"],
                user=request.user,
            )
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not payment.is_paid:
            return Response(
                {"error": "Only paid payments can be refunded."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if payment.status == Payment.Status.REFUNDED:
            return Response(
                {"error": "Already refunded."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refund = stripe.Refund.create(
                payment_intent=payment.payment_intent_id,
                reason=serializer.validated_data.get("reason", "requested_by_customer"),
            )
            payment.status    = Payment.Status.REFUNDED
            payment.refund_id = refund.id
            payment.save()

            return Response({
                "message":   "Refund successful.",
                "refund_id": refund.id,
                "payment":   PaymentSerializer(payment).data,
            }, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# GET /api/payments/history/
# ──────────────────────────────────────────────
class PaymentHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = PaymentSerializer

    @extend_schema(
        summary="To'lovlar tarixi",
        responses={200: PaymentSerializer(many=True)},
        tags=["Payments"],
    )
    def get_queryset(self):
        return Payment.objects.filter(
            user=self.request.user
        ).order_by("-created_at")


# ──────────────────────────────────────────────
# GET /api/payments/{payment_id}/
# ──────────────────────────────────────────────
class PaymentDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = PaymentSerializer
    lookup_field       = "payment_id"

    @extend_schema(
        summary="Bitta to'lov detali",
        responses={200: PaymentSerializer},
        tags=["Payments"],
    )
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


# ──────────────────────────────────────────────
# Stripe Webhook
# ──────────────────────────────────────────────
@csrf_exempt
def stripe_webhook(request):
    payload    = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    data  = event["data"]["object"]
    etype = event["type"]

    if etype == "payment_intent.succeeded":
        Payment.objects.filter(payment_intent_id=data["id"]).update(
            status=Payment.Status.SUCCEEDED,
            is_paid=True,
        )

    elif etype == "payment_intent.payment_failed":
        Payment.objects.filter(payment_intent_id=data["id"]).update(
            status=Payment.Status.FAILED,
        )

    elif etype == "charge.refunded":
        Payment.objects.filter(
            payment_intent_id=data.get("payment_intent")
        ).update(
            status=Payment.Status.REFUNDED,
        )

    return HttpResponse(status=200)