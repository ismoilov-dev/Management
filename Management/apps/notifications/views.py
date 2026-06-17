import json
import uuid
import time
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.db.models import QuerySet

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .models import Notification
from .serializers import (
    NotificationSerializer,
    NotificationBulkReadSerializer,
    NotificationBulkReadResponseSerializer,
    UnreadCountResponseSerializer,
)
from .services import NotificationService


# 1.SSE STREAM VIEW

def sse_stream(request):
    """
    GET /api/notifications/stream/
    
    Browser bu endpoint ga ulanib turadi.
    Server har 2 sekundda pending notiflarni yuboradi.
    Keep-alive ping ham yuboriladi (bağlantı uzilmasin).
    """
    if not request.user.is_authenticated:
        def _deny():
            yield "event: error\ndata: {\"detail\": \"Unauthorized\"}\n\n"
        return StreamingHttpResponse(
            _deny(),
            content_type="text/event-stream",
            status=401,
        )

    def _event_generator():
        user_id = request.user.id
        last_id = 0  
        
        last_event_id = request.META.get("HTTP_LAST_EVENT_ID")
        if last_event_id:
            missed = Notification.objects.filter(
                recipient_id=user_id,
                id__gt=int(last_event_id),
                is_read=False,
            ).order_by("id")
            for n in missed:
                data = NotificationSerializer(n).data
                yield _format_sse(data, event="notification", event_id=n.id)

        while True:
            if hasattr(request, "is_aborted") and request.is_aborted():
                break

            pending = NotificationService.pop_pending(user_id)
            for item in pending:
                last_id = item.get("id", last_id)
                yield _format_sse(item, event="notification", event_id=last_id)

            yield ": ping\n\n"

            time.sleep(2)  

    response = StreamingHttpResponse(
        _event_generator(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  
    return response


def _format_sse(data: dict, event: str = "message", event_id=None) -> str:
    """SSE protokoli formati: id, event, data."""
    lines = []
    if event_id:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event}")
    lines.append(f"data: {json.dumps(data, default=str)}")
    lines.append("\n")  
    return "\n".join(lines)


# 2. REST: Notification ro'yxati

class NotificationListView(generics.ListAPIView):
    """
    GET /api/notifications/
    ?unread=true  →  faqat o'qilmaganlar
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        qs = Notification.objects.filter(
            recipient=self.request.user
        ).select_related("sender")

        if self.request.query_params.get("unread") == "true":
            qs = qs.filter(is_read=False)

        return qs


# 3. REST: Bitta notification o'qilgan deb belgilash

@extend_schema_view(
    patch=extend_schema(
        summary="Bitta notificationni o'qilgan deb belgilash",
        responses={
            200: NotificationSerializer,
            404: OpenApiResponse(description="Topilmadi"),
        },
        tags=["Notifications"],
    ),
)
class NotificationReadView(APIView):
    """PATCH /api/notifications/<pk>/read/"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk: uuid):
        try:
            notif = Notification.objects.get(
                pk=pk, recipient=request.user
            )
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND
            )

        if not notif.is_read:
            notif.is_read = True
            notif.read_at = timezone.now()
            notif.save(update_fields=["is_read", "read_at"])

        return Response(NotificationSerializer(notif).data)


# 4. REST: Hammasini o'qilgan deb belgilash

class NotificationBulkReadView(APIView):
    """POST /api/notifications/mark-all-read/"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Notificationlarni o'qilgan deb belgilash",
        request=NotificationBulkReadSerializer,
        responses={200: NotificationBulkReadResponseSerializer},
        tags=["Notifications"],
    )
    def post(self, request):
        serializer = NotificationBulkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ids = serializer.validated_data.get("ids", [])
        qs = Notification.objects.filter(
            recipient=request.user, is_read=False
        )
        if ids:
            qs = qs.filter(id__in=ids)

        count = qs.update(is_read=True, read_at=timezone.now())
        return Response({"updated": count})


# 5. REST: O'qilmagan soni (badge uchun)

@extend_schema(
    summary="O'qilmagan notificationlar soni",
    responses={200: UnreadCountResponseSerializer},
    tags=["Notifications"],
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def unread_count(request):
    """GET /api/notifications/unread-count/"""
    count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()
    return Response({"unread_count": count})