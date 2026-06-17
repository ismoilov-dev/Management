from django.contrib import admin

from .models import CustomUser, UserSettings, ActionHistory


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "full_name",
        "role",
        "phone",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_filter = ("role", "is_active", "is_staff", "created_at")
    search_fields = ("email", "first_name", "last_name", "middle_name", "phone")
    ordering = ("last_name", "first_name")
    readonly_fields = ("id", "created_at", "updated_at", "last_login")
    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Shaxsiy ma'lumotlar", {
            "fields": ("first_name", "last_name", "middle_name", "phone", "avatar")
        }),
        ("Rol va ruxsatlar", {
            "fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        ("Sanalar", {"fields": ("last_login", "created_at", "updated_at", "deleted_at")}),
    )

    @admin.display(description="To'liq ism")
    def full_name(self, obj):
        return obj.full_name


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "language",
        "theme",
        "email_notifications",
        "sms_notifications",
        "push_notifications",
    )
    list_filter = ("language", "theme", "email_notifications", "sms_notifications", "push_notifications")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    raw_id_fields = ("user",)


@admin.register(ActionHistory)
class ActionHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "actor",
        "action_type",
        "model_name",
        "object_repr",
        "ip_address",
        "created_at",
    )
    list_filter = ("action_type", "model_name", "created_at")
    search_fields = ("actor__email", "model_name", "object_id", "object_repr")
    readonly_fields = (
        "id", "actor", "action_type", "model_name", "object_id",
        "object_repr", "changes", "ip_address", "created_at", "updated_at",
    )
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
