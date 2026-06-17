from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "notif_type",
            "is_read",
            "read_at",
            "link",
            "metadata",
            "sender_name",
            "created_at",
        ]
        read_only_fields = fields

    def get_sender_name(self, obj) -> str | None:
        return obj.sender.get_full_name() if obj.sender else None

class NotificationMarkReadSerializer(serializers.Serializer):
    """PATCH /notifications/<pk>/read/ uchun."""
    # Body shart emas, lekin future uchun bo'sh qoldiramiz
    pass

class NotificationBulkReadSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Bo'sh = barchasi o'qilgan deb belgilanadi",
    )


class NotificationBulkReadResponseSerializer(serializers.Serializer):
    updated = serializers.IntegerField()


class UnreadCountResponseSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()