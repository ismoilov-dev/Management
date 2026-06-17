
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Max, Count, OuterRef, Subquery, F
from apps.chats.models import ChatRoom, ChatParticipant, Message
from .serializers import (
    ChatRoomSerializer,
    ChatRoomCreateSerializer,
    MessageSerializer,
    ChatParticipantSerializer,
)

class ChatRoomListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Oxirgi xabar ma'lumotlarini bitta so'rovda olib kelish uchun Subquery-lar
        last_msg_subquery = Message.objects.filter(room=OuterRef("pk")).order_by("-created_at")
        
        return (
            ChatRoom.objects
            .filter(participants=user)
            .annotate(
                participant_count=Count("participant_links", distinct=True),
                last_message_at=Max("messages__created_at"),
                # Oxirgi xabar detallari:
                last_msg_id=Subquery(last_msg_subquery.values("id")[:1]),
                last_msg_content=Subquery(last_msg_subquery.values("content")[:1]),
                last_msg_type=Subquery(last_msg_subquery.values("msg_type")[:1]),
                last_msg_sender_name=Subquery(last_msg_subquery.values("sender__full_name")[:1]),
                
                # Unread count subquery orqali aniq hisoblash
                unread_count=Count(
                    "messages",
                    filter=Q(
                        messages__created_at__gt=Subquery(
                            ChatParticipant.objects.filter(
                                room=OuterRef("pk"), user=user
                            ).values("last_read_at")[:1]
                        )
                    ),
                    distinct=True
                )
            )
            .order_by("-last_message_at")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ChatRoomCreateSerializer
        return ChatRoomSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MessageListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = MessageSerializer

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        
        if not ChatParticipant.objects.filter(room_id=room_id, user=self.request.user).exists():
            return Message.objects.none()

        qs = Message.objects.filter(room_id=room_id).select_related(
            "sender", "reply_to__sender"
        ).order_by("-created_at")

        cursor = self.request.query_params.get("cursor")
        if cursor:
            qs = qs.filter(id__lt=cursor)

        limit = min(int(self.request.query_params.get("limit", 30)), 100) # Limit xavfsizligi
        return qs[:limit]

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        # Oxirgi xabarlar tartibini to'g'rilash (Eski xabardan yangisiga qarab)
        data = self.get_serializer(reversed(list(qs)), many=True).data
        
        # Cursor-pagination uchun has_more
        limit = min(int(request.query_params.get("limit", 30)), 100)
        has_more = len(qs) == limit
        next_cursor = str(qs.last().id) if has_more and qs.exists() else None
        
        return Response({
            "messages": data, 
            "has_more": has_more,
            "next_cursor": next_cursor
        })


class ChatRoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/chats/rooms/<id>/   → Chat ma'lumotlari
    PATCH  /api/chats/rooms/<id>/   → Nomini o'zgartirish (admin)
    DELETE /api/chats/rooms/<id>/   → Chatni o'chirish (admin)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = ChatRoomSerializer

    def get_queryset(self):
        return ChatRoom.objects.filter(participants=self.request.user)

    def perform_update(self, serializer):
        room = self.get_object()
        self._check_admin(room)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_admin(instance)
        instance.delete()

    def _check_admin(self, room):
        is_admin = ChatParticipant.objects.filter(
            room=room, user=self.request.user, is_admin=True
        ).exists()
        if not is_admin and room.created_by != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Faqat admin o'zgartira oladi")


class MessageListView(generics.ListAPIView):
    """
    GET /api/chats/rooms/<room_id>/messages/?cursor=<id>&limit=30
    Sahifalash: cursor-based (oxirgi xabardan yuqoriga)
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = MessageSerializer

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        # Access check
        if not ChatParticipant.objects.filter(
            room_id=room_id, user=self.request.user
        ).exists():
            return Message.objects.none()

        qs     = Message.objects.filter(room_id=room_id).select_related(
            "sender", "reply_to__sender"
        ).order_by("-created_at")

        cursor = self.request.query_params.get("cursor")
        if cursor:
            qs = qs.filter(id__lt=cursor)

        limit = int(self.request.query_params.get("limit", 30))
        return qs[:limit]

    def list(self, request, *args, **kwargs):
        qs       = self.get_queryset()
        data     = self.get_serializer(reversed(list(qs)), many=True).data
        has_more = len(qs) == int(request.query_params.get("limit", 30))
        return Response({"messages": data, "has_more": has_more})


class ParticipantListView(generics.ListAPIView):
    """
    GET /api/chats/rooms/<room_id>/participants/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = ChatParticipantSerializer

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        if not ChatParticipant.objects.filter(
            room_id=room_id, user=self.request.user
        ).exists():
            return ChatParticipant.objects.none()
        return ChatParticipant.objects.filter(room_id=room_id).select_related("user")


class AddParticipantView(APIView):
    """
    POST /api/chats/rooms/<room_id>/participants/add/
    Body: { "user_id": "uuid" }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        room = self._get_admin_room(room_id)
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "user_id kerak"}, status=400)

        from apps.accounts.models import CustomUser
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "Foydalanuvchi topilmadi"}, status=404)

        obj, created = ChatParticipant.objects.get_or_create(room=room, user=user)
        if not created:
            return Response({"detail": "Allaqachon ishtirokchi"}, status=400)
        return Response({"detail": "Qo'shildi"}, status=201)

    def _get_admin_room(self, room_id):
        room = generics.get_object_or_404(ChatRoom, id=room_id)
        is_admin = ChatParticipant.objects.filter(
            room=room, user=self.request.user, is_admin=True
        ).exists()
        if not is_admin:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Faqat admin qo'sha oladi")
        return room


class RemoveParticipantView(APIView):
    """
    DELETE /api/chats/rooms/<room_id>/participants/<user_id>/remove/
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, room_id, user_id):
        if str(request.user.id) != str(user_id):
            room = generics.get_object_or_404(ChatRoom, id=room_id)
            is_admin = ChatParticipant.objects.filter(
                room=room, user=request.user, is_admin=True
            ).exists()
            if not is_admin:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Ruxsat yo'q")

        deleted, _ = ChatParticipant.objects.filter(
            room_id=room_id, user_id=user_id
        ).delete()
        if not deleted:
            return Response({"detail": "Topilmadi"}, status=404)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LeaveRoomView(APIView):
    """
    POST /api/chats/rooms/<room_id>/leave/
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        deleted, _ = ChatParticipant.objects.filter(
            room_id=room_id, user=request.user
        ).delete()
        if not deleted:
            return Response({"detail": "Siz bu chatda emassiz"}, status=400)
        return Response({"detail": "Chatdan chiqildi"})


class UploadAttachmentView(APIView):
    """
    POST /api/chats/rooms/<room_id>/upload/
    Fayl yuklash va message yaratish
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        if not ChatParticipant.objects.filter(
            room_id=room_id, user=request.user
        ).exists():
            return Response({"detail": "Ruxsat yo'q"}, status=403)

        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "Fayl kerak"}, status=400)

        content_type = file.content_type or ""
        if content_type.startswith("image/"):
            msg_type = "image"
        else:
            msg_type = "file"

        room = ChatRoom.objects.get(id=room_id)
        msg  = Message.objects.create(
            room=room,
            sender=request.user,
            attachment=file,
            msg_type=msg_type,
            content=file.name,
        )
        return Response(MessageSerializer(msg).data, status=201)


class SearchMessagesView(generics.ListAPIView):
    """
    GET /api/chats/rooms/<room_id>/search/?q=<text>
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class   = MessageSerializer

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        query   = self.request.query_params.get("q", "")
        if not query or not ChatParticipant.objects.filter(
            room_id=room_id, user=self.request.user
        ).exists():
            return Message.objects.none()

        return Message.objects.filter(
            room_id=room_id,
            content__icontains=query,
        ).select_related("sender").order_by("-created_at")[:50]