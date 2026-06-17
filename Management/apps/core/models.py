# apps/core/models.py
"""
Core abstract models — barcha app'lar tomonidan meros olinadigan
base class'lar. DRY principle asosida.
"""

from django.utils.text import slugify

import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


# ─────────────────────────────────────────────
# ABSTRACT BASE MODELS
# ─────────────────────────────────────────────

class UUIDModel(models.Model):
    """
    Primary key sifatida UUID ishlatuvchi base model.
    Auto-increment integer ID o'rniga UUID — security uchun.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID"),
    )

    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    """
    Yaratilgan va yangilangan vaqtlarni avtomatik saqlaydi.
    Barcha asosiy modellarga meros qilinadi.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Yaratilgan vaqt"),
        db_index=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Yangilangan vaqt"),
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class SoftDeleteManager(models.Manager):
    """
    Faqat o'chirilmagan (active) objectlarni qaytaradi.
    """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        return super().get_queryset()

    def deleted_only(self):
        return super().get_queryset().filter(deleted_at__isnull=False)


class SoftDeleteModel(models.Model):
    """
    Hard delete o'rniga soft delete — ma'lumot yo'qolmaydi.
    Audit va history uchun muhim.
    """
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("O'chirilgan vaqt"),
        db_index=True,
    )
    deleted_by = models.ForeignKey(
        "accounts.CustomUser",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_deleted",
        verbose_name=_("O'chirgan foydalanuvchi"),
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Hamma, o'chirilganlar ham

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["deleted_at", "deleted_by"])

    def restore(self):
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["deleted_at", "deleted_by"])

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class BaseModel(UUIDModel, TimestampedModel, SoftDeleteModel):
    """
    Asosiy base model — UUID + timestamps + soft delete.
    Ko'pchilik modellar shu'dan meros oladi.
    """
    class Meta:
        abstract = True
        ordering = ["-created_at"]


# ─────────────────────────────────────────────
# SLUG MIXIN
# ─────────────────────────────────────────────

class SlugMixin(models.Model):
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,   
        verbose_name=_("Slug"),
        help_text=_("URL uchun noyob identifikator, bo'sh qolsa avtomatik"),
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)          # name fielddan oladi
            slug = base_slug
            # unique bo'lmasa oxiriga qisqa uuid qo'shadi
            while self.__class__.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            self.slug = slug
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
# ENUMS (choices)
# ─────────────────────────────────────────────

class GenderChoices(models.TextChoices):
    MALE   = "male",   _("Erkak")
    FEMALE = "female", _("Ayol")
    OTHER  = "other",  _("Boshqa")


class LanguageChoices(models.TextChoices):
    UZBEK   = "uz", _("O'zbek")
    RUSSIAN = "ru", _("Rus")
    ENGLISH = "en", _("Ingliz")


class ThemeChoices(models.TextChoices):
    LIGHT = "light", _("Yorug'")
    DARK  = "dark",  _("Qorong'u")