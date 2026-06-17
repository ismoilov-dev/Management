from django.contrib import admin

from .models import ChatRoom, ChatParticipant, Message


class ChatParticipantInline(admin.TabularInline):
    model = ChatParticipant
    extra = 0
    raw_id_fields = ("user",)
    fields = ("user", "is_admin", "joined_at", "last_read_at")
    readonly_fields = ("joined_at",)


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("__str__", "room_type", "created_by", "created_at")
    list_filter = ("room_type", "created_at")
    search_fields = ("name",)
    raw_id_fields = ("created_by",)
    inlines = [ChatParticipantInline]


@admin.register(ChatParticipant)
class ChatParticipantAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "is_admin", "joined_at", "last_read_at")
    list_filter = ("is_admin",)
    search_fields = ("user__email", "room__name")
    raw_id_fields = ("room", "user")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "room", "msg_type", "is_edited", "created_at")
    list_filter = ("msg_type", "is_edited", "created_at")
    search_fields = ("content", "sender__email")
    raw_id_fields = ("room", "sender", "reply_to")
    date_hierarchy = "created_at"
