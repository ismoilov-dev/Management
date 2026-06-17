from rest_framework import serializers
from apps.chats.models import ChatRoom, ChatParticipant, Message


class SenderSerializer(serializers.Serializer):
    id        = serializers.UUIDField()
    full_name = serializers.CharField()
    avatar    = serializers.URLField(allow_null=True)


class MessageSerializer(serializers.ModelSerializer):
    sender     = SenderSerializer(read_only=True)
    reply_to   = serializers.SerializerMethodField()
    attachment = serializers.FileField(use_url=True, allow_null=True, read_only=True)

    class Meta:
        model  = Message
        fields = [
            "id", "content", "msg_type", "sender",
            "attachment", "reply_to",
            "is_edited", "edited_at", "created_at",
        ]

    def get_reply_to(self, obj):
        if not obj.reply_to:
            return None
        return {
            "id":      str(obj.reply_to.id),
            "content": obj.reply_to.content[:100],
            "sender":  obj.reply_to.sender.full_name,
        }


class ChatParticipantSerializer(serializers.ModelSerializer):
    user      = SenderSerializer(read_only=True)
    is_admin  = serializers.BooleanField(read_only=True)
    joined_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model  = ChatParticipant
        fields = ["id", "user", "is_admin", "joined_at", "last_read_at"]


class LastMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.full_name", read_only=True)

    class Meta:
        model  = Message
        fields = ["id", "content", "msg_type", "sender_name", "created_at"]


class ChatRoomSerializer(serializers.ModelSerializer):
    last_message   = serializers.SerializerMethodField()
    unread_count   = serializers.IntegerField(read_only=True, default=0)
    participant_count = serializers.SerializerMethodField()
    participants_preview = serializers.SerializerMethodField()

    class Meta:
        model  = ChatRoom
        fields = [
            "id", "name", "room_type", "created_by",
            "last_message", "unread_count",
            "participant_count", "participants_preview",
            "created_at",
        ]
        read_only_fields = ["created_by", "created_at"]

    def get_last_message(self, obj):
        msg = obj.messages.order_by("-created_at").first()
        if msg:
            return LastMessageSerializer(msg).data
        return None

    def get_participant_count(self, obj):
        return obj.participant_links.count()

    def get_participants_preview(self, obj):
        links = obj.participant_links.select_related("user")[:3]
        return [
            {"id": str(l.user.id), "name": l.user.full_name, "avatar": l.user.avatar}
            for l in links
        ]


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        help_text="Ishtirokchilar ID ro'yxati"
    )

    class Meta:
        model  = ChatRoom
        fields = ["name", "room_type", "participant_ids"]

    def validate(self, attrs):
        room_type = attrs.get("room_type", "personal")
        ids       = attrs.get("participant_ids", [])
        if room_type == "personal" and len(ids) != 1:
            raise serializers.ValidationError(
                "Shaxsiy chat uchun aynan 1 ta ishtirokchi kerak"
            )
        if room_type == "group" and len(ids) < 1:
            raise serializers.ValidationError(
                "Guruh chati uchun kamida 1 ta ishtirokchi kerak"
            )
        return attrs

    def create(self, validated_data):
        from apps.accounts.models import CustomUser
        participant_ids = validated_data.pop("participant_ids")
        creator         = validated_data.pop("created_by")

        room = ChatRoom.objects.create(created_by=creator, **validated_data)

        # Add creator as admin
        ChatParticipant.objects.create(room=room, user=creator, is_admin=True)

        # Add other participants
        for uid in participant_ids:
            try:
                user = CustomUser.objects.get(id=uid)
                if user != creator:
                    ChatParticipant.objects.get_or_create(room=room, user=user)
            except CustomUser.DoesNotExist:
                pass

        return room