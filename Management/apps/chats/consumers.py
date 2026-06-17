import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.db.models import Q


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer for real-time chat.
    
    URL pattern: ws/chat/<room_id>/
    
    Supported events (client → server):
        - send_message     : Xabar yuborish
        - edit_message     : Xabarni tahrirlash
        - delete_message   : Xabarni o'chirish
        - typing           : Yozmoqda holati
        - stop_typing      : Yozishni to'xtatish
        - read_messages    : Xabarlarni o'qilgan deb belgilash
        - react_message    : Emoji reaktsiya (kengaytirilgan)
        
    Server → client events:
        - new_message
        - message_edited
        - message_deleted
        - typing_indicator
        - messages_read
        - user_online / user_offline
        - error
    """

    async def connect(self):
        self.room_id   = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group = f"chat_{self.room_id}"
        self.user       = self.scope["user"]

        # Auth check
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Room access check
        if not await self._is_participant():
            await self.close(code=4003)
            return

        # Join room group
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        # Mark user online
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type":    "user_online",
                "user_id": str(self.user.id),
                "name":    self.user.full_name,
            },
        )

        # Send recent messages on connect
        messages = await self._get_recent_messages(50)
        await self.send(text_data=json.dumps({
            "event":    "init",
            "messages": messages,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, "room_group"):
            await self.channel_layer.group_send(
                self.room_group,
                {
                    "type":    "user_offline",
                    "user_id": str(self.user.id),
                    "name":    self.user.full_name,
                },
            )
            await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        try:
            data  = json.loads(text_data)
            event = data.get("event")
        except (json.JSONDecodeError, AttributeError):
            await self._send_error("Noto'g'ri format")
            return

        handlers = {
            "send_message":   self._handle_send_message,
            "edit_message":   self._handle_edit_message,
            "delete_message": self._handle_delete_message,
            "typing":         self._handle_typing,
            "stop_typing":    self._handle_stop_typing,
            "read_messages":  self._handle_read_messages,
        }

        handler = handlers.get(event)
        if handler:
            await handler(data)
        else:
            await self._send_error(f"Noma'lum event: {event}")

    # ─── Event Handlers ────────────────────────────────────────────────────────

    async def _handle_send_message(self, data):
        content     = data.get("content", "").strip()
        msg_type    = data.get("msg_type", "text")
        reply_to_id = data.get("reply_to_id")

        if not content and msg_type == "text":
            await self._send_error("Xabar bo'sh bo'lishi mumkin emas")
            return

        message = await self._save_message(content, msg_type, reply_to_id)
        if not message:
            await self._send_error("Xabarni saqlashda xato")
            return

        await self.channel_layer.group_send(
            self.room_group,
            {
                "type":    "new_message",
                "message": message,
            },
        )

    async def _handle_edit_message(self, data):
        message_id  = data.get("message_id")
        new_content = data.get("content", "").strip()

        if not new_content:
            await self._send_error("Yangi matn bo'sh bo'lishi mumkin emas")
            return

        result = await self._edit_message(message_id, new_content)
        if not result:
            await self._send_error("Xabarni tahrirlashda xato yoki ruxsat yo'q")
            return

        await self.channel_layer.group_send(
            self.room_group,
            {
                "type":       "message_edited",
                "message_id": str(message_id),
                "content":    new_content,
                "edited_at":  result,
            },
        )

    async def _handle_delete_message(self, data):
        message_id = data.get("message_id")

        success = await self._delete_message(message_id)
        if not success:
            await self._send_error("Xabarni o'chirishda xato yoki ruxsat yo'q")
            return

        await self.channel_layer.group_send(
            self.room_group,
            {
                "type":       "message_deleted",
                "message_id": str(message_id),
                "deleted_by": str(self.user.id),
            },
        )

    async def _handle_typing(self, data):
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type":    "typing_indicator",
                "user_id": str(self.user.id),
                "name":    self.user.full_name,
                "typing":  True,
            },
        )

    async def _handle_stop_typing(self, data):
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type":    "typing_indicator",
                "user_id": str(self.user.id),
                "name":    self.user.full_name,
                "typing":  False,
            },
        )

    async def _handle_read_messages(self, data):
        await self._mark_as_read()
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type":    "messages_read",
                "user_id": str(self.user.id),
                "room_id": self.room_id,
            },
        )

    # ─── Group Message Handlers (server → client) ──────────────────────────────

    async def new_message(self, event):
        await self.send(text_data=json.dumps({
            "event":   "new_message",
            "message": event["message"],
        }))

    async def message_edited(self, event):
        await self.send(text_data=json.dumps({
            "event":      "message_edited",
            "message_id": event["message_id"],
            "content":    event["content"],
            "edited_at":  event["edited_at"],
        }))

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            "event":      "message_deleted",
            "message_id": event["message_id"],
            "deleted_by": event["deleted_by"],
        }))

    async def typing_indicator(self, event):
        if str(self.user.id) != event["user_id"]:
            await self.send(text_data=json.dumps({
                "event":   "typing",
                "user_id": event["user_id"],
                "name":    event["name"],
                "typing":  event["typing"],
            }))

    async def messages_read(self, event):
        await self.send(text_data=json.dumps({
            "event":   "messages_read",
            "user_id": event["user_id"],
            "room_id": event["room_id"],
        }))

    async def user_online(self, event):
        if str(self.user.id) != event["user_id"]:
            await self.send(text_data=json.dumps({
                "event":   "user_online",
                "user_id": event["user_id"],
                "name":    event["name"],
            }))

    async def user_offline(self, event):
        if str(self.user.id) != event["user_id"]:
            await self.send(text_data=json.dumps({
                "event":   "user_offline",
                "user_id": event["user_id"],
                "name":    event["name"],
            }))

    # ─── DB Helpers ────────────────────────────────────────────────────────────

    @database_sync_to_async
    def _is_participant(self):
        from apps.chats.models import ChatParticipant
        return ChatParticipant.objects.filter(
            room_id=self.room_id, user=self.user
        ).exists()

    @database_sync_to_async
    def _save_message(self, content, msg_type, reply_to_id):
        from apps.chats.models import Message, ChatRoom
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            msg  = Message.objects.create(
                room=room,
                sender=self.user,
                content=content,
                msg_type=msg_type,
                reply_to_id=reply_to_id,
            )
            reply_data = None
            if msg.reply_to:
                reply_data = {
                    "id":      str(msg.reply_to.id),
                    "content": msg.reply_to.content[:100],
                    "sender":  msg.reply_to.sender.full_name,
                }
            return {
                "id":         str(msg.id),
                "content":    msg.content,
                "msg_type":   msg.msg_type,
                "sender_id":  str(msg.sender.id),
                "sender":     msg.sender.full_name,
                "avatar":     msg.sender.avatar,
                "created_at": msg.created_at.isoformat(),
                "reply_to":   reply_data,
                "is_edited":  False,
            }
        except Exception:
            return None

    @database_sync_to_async
    def _edit_message(self, message_id, new_content):
        from apps.chats.models import Message
        try:
            msg = Message.objects.get(id=message_id, sender=self.user)
            msg.content   = new_content
            msg.is_edited = True
            msg.edited_at = timezone.now()
            msg.save(update_fields=["content", "is_edited", "edited_at"])
            return msg.edited_at.isoformat()
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def _delete_message(self, message_id):
        from apps.chats.models import Message
        try:
            msg = Message.objects.get(
                id=message_id,
                room_id=self.room_id
            )
            # Only sender or room admin can delete
            is_admin = msg.room.participant_links.filter(
                user=self.user, is_admin=True
            ).exists()
            if str(msg.sender.id) != str(self.user.id) and not is_admin:
                return False
            msg.delete()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def _mark_as_read(self):
        from apps.chats.models import ChatParticipant
        ChatParticipant.objects.filter(
            room_id=self.room_id, user=self.user
        ).update(last_read_at=timezone.now())

    @database_sync_to_async
    def _get_recent_messages(self, limit=50):
        from apps.chats.models import Message
        msgs = (
            Message.objects
            .filter(room_id=self.room_id)
            .select_related("sender", "reply_to__sender")
            .order_by("-created_at")[:limit]
        )
        result = []
        for msg in reversed(list(msgs)):
            reply_data = None
            if msg.reply_to:
                reply_data = {
                    "id":      str(msg.reply_to.id),
                    "content": msg.reply_to.content[:100],
                    "sender":  msg.reply_to.sender.full_name,
                }
            result.append({
                "id":         str(msg.id),
                "content":    msg.content,
                "msg_type":   msg.msg_type,
                "sender_id":  str(msg.sender.id),
                "sender":     msg.sender.full_name,
                "avatar":     msg.sender.avatar,
                "created_at": msg.created_at.isoformat(),
                "reply_to":   reply_data,
                "is_edited":  msg.is_edited,
                "edited_at":  msg.edited_at.isoformat() if msg.edited_at else None,
            })
        return result

    async def _send_error(self, message):
        await self.send(text_data=json.dumps({
            "event":   "error",
            "message": message,
        }))


# ─── Presence / Online Consumer ────────────────────────────────────────────────

class PresenceConsumer(AsyncWebsocketConsumer):
    """
    Global online holatini kuzatish uchun.
    ws/presence/
    """

    async def connect(self):
        self.user = self.scope["user"]
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = f"presence_{self.user.id}"
        await self.channel_layer.group_add("presence_global", self.channel_name)
        await self.accept()

        # Broadcast online
        await self.channel_layer.group_send(
            "presence_global",
            {
                "type":    "presence_update",
                "user_id": str(self.user.id),
                "online":  True,
            },
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            "presence_global",
            {
                "type":    "presence_update",
                "user_id": str(self.user.id),
                "online":  False,
            },
        )
        await self.channel_layer.group_discard("presence_global", self.channel_name)

    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            "event":   "presence",
            "user_id": event["user_id"],
            "online":  event["online"],
        }))