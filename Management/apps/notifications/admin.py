from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "recipient",
        "sender",
        "notif_type",
        "is_read",
        "read_at",
        "created_at",
    )
    list_filter = ("notif_type", "is_read", "created_at")
    search_fields = ("title", "message", "recipient__email")
    raw_id_fields = ("recipient", "sender")
    date_hierarchy = "created_at"
    readonly_fields = ("read_at",)
