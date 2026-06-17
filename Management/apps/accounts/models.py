from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    UUIDModel,
    TimestampedModel,
    GenderChoices,
    LanguageChoices,
    ThemeChoices,
)


class RoleChoices(models.TextChoices):
    SUPER_ADMIN = "super_admin", _("Super Admin")
    ADMIN       = "admin",       _("Admin")
    TEACHER     = "teacher",     _("O'qituvchi")
    STUDENT     = "student",     _("Talaba")
    PARENT      = "parent",      _("Ota-ona")


class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email manzil kiritilishi shart"))
        email = self.normalize_email(email)
        extra_fields.setdefault("role", RoleChoices.STUDENT)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", RoleChoices.SUPER_ADMIN)
        extra_fields.setdefault("first_name", "Super")
        extra_fields.setdefault("last_name", "Admin")
        return self.create_user(email, password, **extra_fields)

    def get_queryset(self):
        
        return super().get_queryset().filter(deleted_at__isnull=True)


class CustomUser(AbstractBaseUser, PermissionsMixin, UUIDModel, TimestampedModel):

    email = models.EmailField(
        unique=True,
        verbose_name=_("Email manzil"),
        db_index=True,
    )
    phone = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Telefon raqam"),
    )
    first_name = models.CharField(
        max_length=100,
        blank=True,          
        verbose_name=_("Ism"),
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,          
        verbose_name=_("Familiya"),
    )
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Otasining ismi"),
    )
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.STUDENT,
        verbose_name=_("Rol"),
        db_index=True,
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Faolmi"),
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name=_("Xodimmi"),
    )
    avatar = models.URLField(
    null=True,
    blank=True,
    verbose_name=_("Avatar")
    )

    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = CustomUserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = []  

    class Meta:
        verbose_name        = _("Foydalanuvchi")
        verbose_name_plural = _("Foydalanuvchilar")
        ordering            = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["email", "role"]),
            models.Index(fields=["role", "is_active"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"

    @property
    def full_name(self):
        parts = filter(None, [self.last_name, self.first_name, self.middle_name])
        return " ".join(parts) or self.email

    # Role helper properties
    @property
    def is_super_admin(self):
        return self.role == RoleChoices.SUPER_ADMIN

    @property
    def is_admin(self):
        return self.role in (RoleChoices.SUPER_ADMIN, RoleChoices.ADMIN)

    @property
    def is_teacher(self):
        return self.role == RoleChoices.TEACHER

    @property
    def is_student(self):
        return self.role == RoleChoices.STUDENT

    @property
    def is_parent(self):
        return self.role == RoleChoices.PARENT




class UserSettings(UUIDModel, TimestampedModel):

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="settings",
        verbose_name=_("Foydalanuvchi"),
    )
    language = models.CharField(
        max_length=5,
        choices=LanguageChoices.choices,
        default=LanguageChoices.UZBEK,
        verbose_name=_("Til"),
    )
    theme = models.CharField(
        max_length=10,
        choices=ThemeChoices.choices,
        default=ThemeChoices.LIGHT,
        verbose_name=_("Tema"),
    )
    email_notifications = models.BooleanField(default=True, verbose_name=_("Email xabarnomalar"))
    sms_notifications   = models.BooleanField(default=True, verbose_name=_("SMS xabarnomalar"))
    push_notifications  = models.BooleanField(default=True, verbose_name=_("Push xabarnomalar"))

    class Meta:
        verbose_name        = _("Foydalanuvchi sozlamalari")
        verbose_name_plural = _("Foydalanuvchilar sozlamalari")

    def __str__(self):
        return f"{self.user.full_name} — Sozlamalar"


class ActionHistory(UUIDModel, TimestampedModel):
    """
    Super Admin uchun audit log.
    Faqat CREATE, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT yoziladi.
    GET so'rovlar yozilmaydi.
    """

    class ActionType(models.TextChoices):
        CREATE = "create", _("Yaratdi")
        UPDATE = "update", _("Yangiladi")
        DELETE = "delete", _("O'chirdi")
        LOGIN  = "login",  _("Kirdi")
        LOGOUT = "logout", _("Chiqdi")
        EXPORT = "export", _("Eksport qildi")

    actor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="action_history",
        verbose_name=_("Harakat qiluvchi"),
        db_index=True,
    )
    action_type = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        verbose_name=_("Harakat turi"),
        db_index=True,
    )
    model_name = models.CharField(
        max_length=100,
        verbose_name=_("Model nomi"),
        db_index=True,
    )
    object_id = models.CharField(
        max_length=36,
        blank=True,
        verbose_name=_("Object ID"),
    )
    object_repr = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Object ko'rinishi"),
    )
    changes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("O'zgarishlar"),
        help_text=_("{'field': ['eski_qiymat', 'yangi_qiymat']} formatida"),
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP manzil"),
    )

    class Meta:
        verbose_name        = _("Harakat tarixi")
        verbose_name_plural = _("Harakat tarixi")
        ordering            = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "action_type"]),
            models.Index(fields=["model_name", "object_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.actor.full_name} | {self.action_type} | {self.model_name}"