# apps/chats/models.py
 
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
 
 
class ChatRoom(BaseModel):
    """
    Xabarlar uchun chat xonasi.
    group chat yoki personal (2 kishi) bo'lishi mumkin.
    """
 
    class RoomType(models.TextChoices):
        PERSONAL = "personal", _("Shaxsiy")
        GROUP    = "group",    _("Guruh chati")
 
    name         = models.CharField(max_length=255, blank=True, verbose_name=_("Nomi"))
    room_type    = models.CharField(
        max_length=10, choices=RoomType.choices, default=RoomType.PERSONAL
    )
    participants = models.ManyToManyField(
        "accounts.CustomUser",
        through="ChatParticipant",
        through_fields=('room' , 'user'),
        related_name="chat_rooms",
        verbose_name=_("Ishtirokchilar"),
    )
    created_by = models.ForeignKey(
        "accounts.CustomUser", null=True, on_delete=models.SET_NULL,
        related_name="created_chats",
    )
 
    class Meta:
        verbose_name        = _("Chat xonasi")
        verbose_name_plural = _("Chat xonalari")
 
    def __str__(self):
        return self.name or f"Chat #{self.id}"
 
 
class ChatParticipant(BaseModel):
    """Ishtirokchi through modeli."""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="participant_links")
    user = models.ForeignKey(
        "accounts.CustomUser", on_delete=models.CASCADE, related_name="chat_links"
    )
    is_admin     = models.BooleanField(default=False)
    joined_at    = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        unique_together = [["room", "user"]]
 
 
class Message(BaseModel):
    """Xabar."""
 
    class MessageType(models.TextChoices):
        TEXT  = "text",  _("Matn")
        FILE  = "file",  _("Fayl")
        IMAGE = "image", _("Rasm")
 
    room       = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="messages", db_index=True
    )
    sender     = models.ForeignKey(
        "accounts.CustomUser", on_delete=models.CASCADE, related_name="sent_messages"
    )
    content    = models.TextField(blank=True, verbose_name=_("Matn"))
    attachment = models.FileField(
        upload_to="chats/%Y/%m/", null=True, blank=True
    )
    msg_type   = models.CharField(
        max_length=10, choices=MessageType.choices, default=MessageType.TEXT
    )
    is_edited  = models.BooleanField(default=False)
    edited_at  = models.DateTimeField(null=True, blank=True)
    reply_to   = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replies"
    )
 
    class Meta:
        verbose_name        = _("Xabar")
        verbose_name_plural = _("Xabarlar")
        ordering            = ["created_at"]
        indexes = [
            models.Index(fields=["room", "created_at"]),
            models.Index(fields=["sender", "created_at"]),
        ]
 
    def __str__(self):
        return f"{self.sender.full_name}: {self.content[:50]}"