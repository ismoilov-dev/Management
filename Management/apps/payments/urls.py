from django.urls import path
from .views import (
    CreatePaymentIntentView,
    ConfirmPaymentView,
    RefundPaymentView,
    PaymentHistoryView,
    PaymentDetailView,
    stripe_webhook,
)

urlpatterns = [
    path("create-intent/", CreatePaymentIntentView.as_view(), name="payment-create-intent"),
    path("confirm/",        ConfirmPaymentView.as_view(),       name="payment-confirm"),
    path("refund/",         RefundPaymentView.as_view(),        name="payment-refund"),
    path("history/",        PaymentHistoryView.as_view(),       name="payment-history"),
    path("<uuid:payment_id>/", PaymentDetailView.as_view(),     name="payment-detail"),
    path("webhook/",        stripe_webhook,                     name="stripe-webhook"),
]