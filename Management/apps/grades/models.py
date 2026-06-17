# apps/grades/models.py
"""
Baho tizimi — kredit-modul asosida.
GradeType: oraliq, yakuniy, mustaqil ish va h.k.
Grade: talabaning fan bo'yicha bahosi.
GPA: semestr/umumiy GPA hisob-kitob natijasi.
"""
 
# apps/grades/models.py
"""
BAHO TIZIMI MODELLARI
=====================

Bu modulda talabalarning baholari, GPA va akademik samaradorlik bilan
bog'liq modellar ta'rif qilingan.

Asosiy modellar:
- Grade: Har bir talabaning har bir fanni baho
- SemesterGPA: Semestr oxirida hisoblab chiqilgan GPA

Baho turlari:
- Oraliq nazorat: Semestr davomida
- Yakuniy nazorat: Semestr oxirida
- Uyga vazifa: Mustaqil ish
- Loyiha: Amaliy loyihalar
- Test: Qisqa testlar

Tizim avtomatik GPA'ni hisoblaydi va signallari orqali yangilaydi.
"""

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel


class Grade(BaseModel):
    """
    BAHO MODELI
    ===========
    
    Talabaning biror fan bo'yicha baholari.
    Har bir baho o'qituvchi tomonidan qo'yiladi va quyidagi ma'lumotlarni saqlaydi:
    - Talaba va fan
    - Baho turi (oraliq, yakuniy, uy vazifasi va h.k.)
    - Ball va maksimal ball
    - Baholash sanasi
    - Izoh/sharh
    
    Database qisqartirlash uchun indexes qo'shilgan:
    - (student, subject): Talabaning biror fan baholarini tezda olish
    - (student, grade_type): Talabaning baho turi bo'yicha baholarni olish
    - (group, subject): Guruh bo'yicha fanini stat hisoblash
    """

    class GradeType(models.TextChoices):
        """
        BAHO TURLARI
        ============
        
        value (DB) | display (UI)
        """
        # value (DB'da saqlanadi) | display (foydalanuvchiga ko'rsatiladi)
        MIDTERM  = "midterm",  _("Oraliq nazorat")     # Semestr o'rtasida
        FINAL    = "final",    _("Yakuniy nazorat")    # Semestr oxirida
        HOMEWORK = "homework", _("Uyga vazifa")        # Mustaqil ish
        PROJECT  = "project",  _("Loyiha")             # Amaliy loyihalar
        QUIZ     = "quiz",     _("Test")               # Qisqa testlar

    # ============= ASOSIY BOG'LANISHLAR =============
    
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,  # Talaba o'chirilsa uning bahosi ham o'chadi
        related_name="grades",     # StudentProfile.grades.all() bilan kirish
        verbose_name=_("Talaba"),
        db_index=True,  # Tez qidiruv uchun index
    )
    """Baho kim uchun: Talaba profiliga bog'lanish."""
    
    subject = models.ForeignKey(
        "courses.Subject",
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name=_("Fan"),
    )
    """Qaysi fan bo'yicha baho: Fan modeligiga bog'lanish."""
    
    teacher = models.ForeignKey(
        "teachers.TeacherProfile",
        on_delete=models.CASCADE,
        related_name="given_grades",
        verbose_name=_("O'qituvchi"),
    )
    """Kim tomonidan baholandi: O'qituvchi profiliga bog'lanish."""
    
    group = models.ForeignKey(
        "groups.Group",
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name=_("Guruh"),
    )
    """Qaysi guruh uchun: Guruh modeligiga bog'lanish."""

    # ============= BAHO MA'LUMOTLARI =============
    
    grade_type = models.CharField(
        max_length=20,
        choices=GradeType.choices,
        verbose_name=_("Baho turi"),
        db_index=True,  # Tez filtrlash uchun
    )
    """Baho turi: oraliq, yakuniy, uyga vazifa va h.k."""
    
    score = models.DecimalField(
        max_digits=5,           # Jami 5 xonali (max 999.99)
        decimal_places=2,       # 2 xonali o'nlik (82.50)
        validators=[
            MinValueValidator(0),      # Minimum 0
            MaxValueValidator(100),    # Maximum 100
        ],
        verbose_name=_("Ball (0–100)"),
    )
    """Talaba olingan ball (0 dan 100 gacha)."""
    
    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100,
        verbose_name=_("Maksimal ball"),
    )
    """Test/imtihon maksimal bali (odatda 100)."""
    
    graded_at = models.DateField(verbose_name=_("Baholash sanasi"))
    """Baho qachon qo'yilgani."""
    
    comment = models.TextField(
        blank=True,
        verbose_name=_("Izoh"),
    )
    """O'qituvchining izohi (majburiy emas)."""

    # ============= META SOZLAMALAR =============
    
    class Meta:
        verbose_name = _("Baho")
        verbose_name_plural = _("Baholar")
        
        # Standart tartib: eng so'nggi baholari avvali
        ordering = ["-graded_at"]
        
        # Database performance uchun indexlar
        indexes = [
            models.Index(fields=["student", "subject"]),
            models.Index(fields=["student", "grade_type"]),
            models.Index(fields=["group", "subject"]),
        ]

    # ============= USUL VA XUSUSIYATLAR =============
    
    def __str__(self):
        """
        Baho ning matn ko'rinishi.
        
        Misollar:
            Abdullayev Adham | Matematika | 85.50
        """
        return f"{self.student.full_name} | {self.subject.name} | {self.score}"

    @property
    def percentage(self):
        """
        Foiz bo'yicha baho.
        
        Hisoblash: (score / max_score) * 100
        
        Misollar:
            Agar score=85, max_score=100 bo'lsa percentage=85.0
            Agar score=42.5, max_score=50 bo'lsa percentage=85.0
        """
        if self.max_score:
            return round((self.score / self.max_score) * 100, 2)
        return 0

    @property
    def letter_grade(self):
        """
        Harf baho (A, B, C, D, F).
        
        Konversiya:
        - 90-100: A (A'lo)
        - 80-89: B (Yaxshi)
        - 70-79: C (O'rtacha)
        - 60-69: D (Qoniqarli)
        - <60: F (Qoniqarsiz)
        """
        if self.score >= 90:
            return 'A'
        elif self.score >= 80:
            return 'B'
        elif self.score >= 70:
            return 'C'
        elif self.score >= 60:
            return 'D'
        else:
            return 'F'

    @property
    def is_passed(self):
        """
        Talaba bu fanni o'tdimi yoki qoldimi (60 dan yuqori o'tgan).
        
        Returns:
            bool: True agar o'tgan bo'lsa, False agar qolgan bo'lsa
        """
        return self.score >= 60


class SemesterGPA(BaseModel):
    """
    SEMESTR GPA MODELI
    ==================
    
    Har semestr tugagandan keyin talabaning semestr davomida olingan
    barcha baholari asosida hisoblangan GPA (Grade Point Average).
    
    Bu model avtomatik ravishda yangilanadi:
    - Signal'lar orqali: Yangi baho qo'shilgan yoki tahrirlanganda
    - Task'lar orqali: Semestr oxirida manual hisoblash uchun
    
    Attributlar:
    - GPA: 0-4 skalada (4.0 = A'lo, 0.0 = Qoniqarsiz)
    - total_credits: Semestrda o'qiydigan jami kreditlar
    - earned_credits: Olingan (o'tgan) kreditlar
    
    Unique constraint: Bitta talaba bir yilda bir semestr uchun faqat bitta GPA
    """
    
    # ============= BOG'LANISHLAR =============
    
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="semester_gpas",
        verbose_name=_("Talaba"),
    )
    """Qaysi talaba uchun: Talaba profiliga bog'lanish."""

    # ============= SEMESTR MA'LUMOTLARI =============
    
    semester = models.PositiveSmallIntegerField(verbose_name=_("Semestr"))
    """Semestr raqami: 1 yoki 2 (juda kam holatlarda 3)."""
    
    year = models.PositiveSmallIntegerField(verbose_name=_("O'quv yili"))
    """O'quv yili: 2023, 2024, 2025 va h.k."""

    # ============= GPA VA KREDITLAR =============
    
    gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(0),    # Minimum 0.0
            MaxValueValidator(4),    # Maximum 4.0
        ],
        verbose_name=_("GPA"),
    )
    """
    Semestr GPA (0-4 skalada).
    
    Hisoblash:
    - O'rtacha: Barcha baholari o'rtacha olib, 0-100 dan 0-4 ga konvertlanadi
    - 90-100: 4.0 (A)
    - 80-89: 3.0 (B)
    - 70-79: 2.0 (C)
    - 60-69: 1.0 (D)
    - <60: 0.0 (F)
    """
    
    total_credits = models.PositiveSmallIntegerField(
        verbose_name=_("Jami kreditlar"),
    )
    """
    Semestrda o'qiydigan jami kreditlar.
    Odatda 60 kredit/semestr (3 yillik dastur uchun 180 kredit jami).
    """
    
    earned_credits = models.PositiveSmallIntegerField(
        verbose_name=_("Olingan kreditlar"),
    )
    """
    Faqat o'tgan (60+ ball) fanlarning kreditlari.
    Balos fanlari kreditlari qayta'n olinishi kerak.
    """

    # ============= META SOZLAMALAR =============
    
    class Meta:
        verbose_name = _("Semestr GPA")
        verbose_name_plural = _("Semestr GPA'lar")
        
        # Bitta talaba bir yilda bir semestr uchun faqat bitta GPA
        unique_together = [["student", "semester", "year"]]
        
        # Yil va semestr bo'yicha tartibi
        ordering = ["year", "semester"]

    # ============= USUL VA XUSUSIYATLAR =============
    
    def __str__(self):
        """
        Semestr GPA ning matn ko'rinishi.
        
        Misollar:
            Abdullayev Adham | 2024-1-sem | GPA: 3.45
        """
        return f"{self.student.full_name} | {self.year}-{self.semester}-sem | GPA: {self.gpa}"

    @property
    def credit_earned_percentage(self):
        """
        Olingan kreditlarning foizi.
        
        Hisoblash: (earned_credits / total_credits) * 100
        
        Misollar:
            Agar earned=60, total=60 bo'lsa: 100%
            Agar earned=55, total=60 bo'lsa: 91.67%
        """
        if self.total_credits > 0:
            return round((self.earned_credits / self.total_credits) * 100, 2)
        return 0

    @property
    def is_excellent_gpa(self):
        """GPA a'lo darajadami (3.5 va undan yuqori)."""
        return self.gpa >= 3.5

    @property
    def is_passed_semester(self):
        """
        Talaba semestrni o'tdimi yoki qoldimi.
        O'tish shurti: Barcha fanlar bo'yicha o'tgan bo'lish.
        """
        return self.gpa >= 1.0  # D darajasi minimum 