import json
from django.utils import timezone
from django.core.cache import cache

from .models import Notification
from .serializers import NotificationSerializer


SSE_CACHE_KEY = "user_{user_id}_sse_queue"
SSE_QUEUE_TTL = 60 * 10  # 10 daqiqa


class NotificationService:

    @classmethod
    def send(
        cls,
        recipient,
        title: str,
        message: str,
        notif_type: str = Notification.NotifType.INFO,
        sender=None,
        link: str = "",
        metadata: dict = None,
    ) -> Notification:
        notif = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            title=title,
            message=message,
            notif_type=notif_type,
            link=link,
            metadata=metadata or {},
        )

        cls._push_to_sse_queue(notif)

        return notif

    @classmethod
    def _push_to_sse_queue(cls, notif: Notification) -> None:
        key = SSE_CACHE_KEY.format(user_id=notif.recipient_id)
        queue: list = cache.get(key, [])

        data = NotificationSerializer(notif).data
        data["created_at"] = notif.created_at.isoformat()
        queue.append(data)

        cache.set(key, queue[-50:], timeout=SSE_QUEUE_TTL)

    @classmethod
    def pop_pending(cls, user_id: int) -> list[dict]:
        key = SSE_CACHE_KEY.format(user_id=user_id)
        queue = cache.get(key, [])
        if queue:
            cache.delete(key)
        return queue