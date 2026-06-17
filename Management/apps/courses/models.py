from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel, SlugMixin


# FACULTY

class Faculty(BaseModel, SlugMixin):
    """
    Oliy ta'lim: Fakultet.
    O'quv markazi uchun: Yo'nalish bo'limi.
    """
    name = models.CharField(
        max_length=255,
        verbose_name=_("Fakultet nomi"),
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Kod"),
        help_text=_("Masalan: CS, MATH, ECO"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Tavsif"),
    )
    dean = models.ForeignKey(
        "teachers.TeacherProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="faculty_dean",
        verbose_name=_("Dekan"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Faolmi"))

    class Meta:
        verbose_name        = _("Fakultet")
        verbose_name_plural = _("Fakultetlar")
        ordering            = ["name"]

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────
# DEPARTMENT
# ─────────────────────────────────────────────

class Department(BaseModel, SlugMixin):
    """Kafedra — Fakultet ichida."""
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name="departments",
        verbose_name=_("Fakultet"),
        db_index=True,
    )
    name = models.CharField(max_length=255, verbose_name=_("Kafedra nomi"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Kod"))
    head = models.ForeignKey(
        "teachers.TeacherProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="department_head",
        verbose_name=_("Kafedra mudiri"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Faolmi"))

    class Meta:
        verbose_name        = _("Kafedra")
        verbose_name_plural = _("Kafedralar")
        ordering            = ["faculty__name", "name"]
        unique_together     = [["faculty", "name"]]

    def __str__(self):
        return f"{self.faculty.name} — {self.name}"


# ─────────────────────────────────────────────
# COURSE (Yo'nalish / Kurs turi)
# ─────────────────────────────────────────────

class Course(BaseModel, SlugMixin):
    """
    Ta'lim yo'nalishi yoki kurs.
    Masalan: 'Kompyuter Injiniringi', 'Python dasturlash' va h.k.
    """

    class LevelChoices(models.TextChoices):
        BACHELOR = "bachelor", _("Bakalavr")
        MASTER   = "master",   _("Magistr")
        PHD      = "phd",      _("PhD")
        DIPLOMA  = "diploma",  _("Diplom")
        COURSE   = "course",   _("Qisqa muddatli kurs")

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name=_("Kafedra"),
        db_index=True,
    )
    name = models.CharField(max_length=255, verbose_name=_("Kurs nomi"))
    code = models.CharField(max_length=20, unique=True, verbose_name=_("Kod"))
    level = models.CharField(
        max_length=20,
        choices=LevelChoices.choices,
        verbose_name=_("Daraja"),
    )
    duration_months = models.PositiveSmallIntegerField(
        verbose_name=_("Davomiyligi (oy)"),
    )
    credit_hours = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("Kredit soatlar"),
    )
    description  = models.TextField(blank=True, verbose_name=_("Tavsif"))
    price        = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Narxi (so'm)"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Faolmi"))

    class Meta:
        verbose_name        = _("Kurs")
        verbose_name_plural = _("Kurslar")
        ordering            = ["department__name", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


# ─────────────────────────────────────────────
# SUBJECT (Fan)
# ─────────────────────────────────────────────

class Subject(BaseModel, SlugMixin):
    """
    Kurs ichidagi alohida fan.
    Masalan: 'Matematika', 'Algoritmlar va ma'lumotlar strukturasi'.
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="subjects",
        verbose_name=_("Kurs"),
        db_index=True,
    )
    name             = models.CharField(max_length=255, verbose_name=_("Fan nomi"))
    code             = models.CharField(max_length=20, verbose_name=_("Kod"))
    credit_hours     = models.PositiveSmallIntegerField(verbose_name=_("Kredit soatlar"))
    semester         = models.PositiveSmallIntegerField(verbose_name=_("Semestr raqami"))
    description      = models.TextField(blank=True, verbose_name=_("Tavsif"))
    is_elective      = models.BooleanField(default=False, verbose_name=_("Tanlov fanmi"))

    class Meta:
        verbose_name        = _("Fan")
        verbose_name_plural = _("Fanlar")
        ordering            = ["course__name", "semester", "name"]
        unique_together     = [["course", "code"]]
        indexes = [
            models.Index(fields=["course", "semester"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.course.name} — {self.semester}-semestr)"


# ─────────────────────────────────────────────
# ROOM (Auditoriya/Xona)
# ─────────────────────────────────────────────

class Room(BaseModel):
    """
    Auditoriya yoki xona.
    Jadval tuzishda band/bo'sh nazorat qilinadi.
    """

    class RoomType(models.TextChoices):
        LECTURE   = "lecture",   _("Ma'ruza xonasi")
        LAB       = "lab",       _("Laboratoriya")
        SEMINAR   = "seminar",   _("Seminar xonasi")
        COMPUTER  = "computer",  _("Kompyuter xonasi")
        SPORTS    = "sports",    _("Sport zali")

    name     = models.CharField(max_length=100, verbose_name=_("Xona nomi/raqami"))
    building = models.CharField(max_length=100, verbose_name=_("Bino"))
    floor    = models.SmallIntegerField(verbose_name=_("Qavat"))
    capacity = models.PositiveSmallIntegerField(verbose_name=_("Sig'imi (kishilar)"))
    room_type = models.CharField(
        max_length=20,
        choices=RoomType.choices,
        default=RoomType.LECTURE,
        verbose_name=_("Xona turi"),
    )
    has_projector  = models.BooleanField(default=False, verbose_name=_("Proyektor bormi"))
    has_computer   = models.BooleanField(default=False, verbose_name=_("Kompyuter bormi"))
    has_whiteboard = models.BooleanField(default=True,  verbose_name=_("Doska bormi"))
    is_active      = models.BooleanField(default=True,  verbose_name=_("Faolmi"))

    class Meta:
        verbose_name        = _("Xona")
        verbose_name_plural = _("Xonalar")
        ordering            = ["building", "floor", "name"]
        unique_together     = [["building", "name"]]

    def __str__(self):
        return f"{self.name} ({self.building}, {self.floor}-qavat)"