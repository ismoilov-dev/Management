# apps/grades/utils.py
"""
GRADES APP UTILITY FUNKSIYALAR
================================

Bu faylda biznes logika (business logic) funksiyalari yozilgan.
View'lar sodda bo'lishi uchun hisoblash va qayta ishlash logikasi shu yerda.

Funksiyalar ro'yxati:
- score_to_gpa_point()            : Ballni GPA punktiga aylantirish
- calculate_gpa_from_grades()     : Baholar ro'yxatidan GPA hisoblash
- calculate_student_gpa_summary() : Talabaning to'liq GPA xulosasini hisoblash
- get_grade_distribution()        : Harf baholar taqsimotini hisoblash
- get_student_subject_grades()    : Talabaning bitta fandagi barcha baholari
- get_group_subject_statistics()  : Guruh va fan bo'yicha statistika
"""

from decimal import Decimal
from django.db.models import Avg, Count, Max, Min, Q

from .models import Grade, SemesterGPA


# ============================================================
# GPA HISOBLASH FUNKSIYALARI
# ============================================================

def score_to_gpa_point(score: float) -> float:
    if score >= 90:
        return 4.0
    elif score >= 80:
        return 3.0
    elif score >= 70:
        return 2.0
    elif score >= 60:
        return 1.0
    else:
        return 0.0


def calculate_gpa_from_grades(grades_queryset) -> float:
    if not grades_queryset.exists():
        return 0.0
    total_points = 0.0
    count        = 0
    for grade in grades_queryset:
        total_points += score_to_gpa_point(float(grade.score))
        count        += 1

    return round(total_points / count, 2) if count > 0 else 0.0


def calculate_weighted_gpa(grades_with_credits: list) -> float:
    if not grades_with_credits:
        return 0.0

    total_points  = 0.0
    total_credits = 0

    for item in grades_with_credits:
        gpa_point      = score_to_gpa_point(float(item["score"]))
        credits        = item["credits"]
        total_points  += gpa_point * credits
        total_credits += credits

    return round(total_points / total_credits, 2) if total_credits > 0 else 0.0


# ============================================================
# STATISTIKA FUNKSIYALARI
# ============================================================

def get_grade_distribution(grades_queryset) -> dict:
    distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for grade in grades_queryset:
        letter             = grade.letter_grade
        distribution[letter] += 1

    return distribution


def get_group_subject_statistics(group_id, subject_id) -> dict:
    grades = Grade.objects.filter(
        group=group_id,
        subject=subject_id,
    )

    if not grades.exists():
        return {
            "total_grades" : 0,
            "average_score": 0.0,
            "max_score"    : 0.0,
            "min_score"    : 0.0,
            "pass_count"   : 0,
            "fail_count"   : 0,
            "pass_rate"    : 0.0,
            "distribution" : {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
            "gpa"          : 0.0,
        }

    aggregates = grades.aggregate(
        avg_score = Avg("score"),
        max_score = Max("score"),
        min_score = Min("score"),
    )

    total_grades = grades.count()
    pass_count = grades.filter(score__gte=60).count()
    fail_count = total_grades - pass_count
    pass_rate = round((pass_count / total_grades) * 100, 2) if total_grades > 0 else 0.0

    return {
        "total_grades" : total_grades,
        "average_score": round(float(aggregates["avg_score"] or 0), 2),
        "max_score"    : float(aggregates["max_score"] or 0),
        "min_score"    : float(aggregates["min_score"] or 0),
        "pass_count"   : pass_count,
        "fail_count"   : fail_count,
        "pass_rate"    : pass_rate,
        "distribution" : get_grade_distribution(grades),
        "gpa"          : calculate_gpa_from_grades(grades),
    }


def get_student_subject_grades(student_id, subject_id) -> dict:
    grades = Grade.objects.filter(
        student=student_id,
        subject=subject_id,
    ).order_by("graded_at")

    if not grades.exists():
        return {
            "grades"       : [],
            "average_score": 0.0,
            "total_grades" : 0,
            "is_passed"    : False,
            "letter_grade" : "F",
            "gpa_point"    : 0.0,
        }

    avg_result    = grades.aggregate(avg=Avg("score"))
    average_score = round(float(avg_result["avg"] or 0), 2)

    if average_score >= 90:
        letter_grade = "A"
    elif average_score >= 80:
        letter_grade = "B"
    elif average_score >= 70:
        letter_grade = "C"
    elif average_score >= 60:
        letter_grade = "D"
    else:
        letter_grade = "F"

    return {
        "grades"       : grades,
        "average_score": average_score,
        "total_grades" : grades.count(),
        "is_passed"    : average_score >= 60,
        "letter_grade" : letter_grade,
        "gpa_point"    : score_to_gpa_point(average_score),
    }


def calculate_student_gpa_summary(student_id) -> dict:
    semester_gpas = SemesterGPA.objects.filter(
        student=student_id,
    ).select_related("student").order_by("year", "semester")

    if not semester_gpas.exists():
        return None

    agg = semester_gpas.aggregate(
        avg_gpa         = Avg("gpa"),
        total_attempted = models_sum("total_credits"),
        total_earned    = models_sum("earned_credits"),
    )

    all_grades        = Grade.objects.filter(student=student_id)
    grade_distribution = get_grade_distribution(all_grades)
    student = semester_gpas.first().student
    return {
        "student_id"             : student.id,
        "student_name"           : student.full_name,
        "overall_gpa"            : round(float(agg["avg_gpa"] or 0), 2),
        "total_semesters"        : semester_gpas.count(),
        "total_credits_attempted": agg["total_attempted"] or 0,
        "total_credits_earned"   : agg["total_earned"] or 0,
        "semester_gpas"          : semester_gpas,
        "grade_distribution"     : grade_distribution,
    }

def models_sum(field_name):
    from django.db.models import Sum
    return Sum(field_name)

# ============================================================
# GRADE TYPE BO'YICHA FILTRLASH
# ============================================================
def get_grades_by_type(student_id, grade_type: str) -> "QuerySet":
    return Grade.objects.filter(
        student    = student_id,
        grade_type = grade_type,
    ).select_related("subject", "teacher").order_by("-graded_at")

def get_recent_grades(student_id, limit: int = 10) -> "QuerySet":
    return Grade.objects.filter(
        student=student_id,
    ).select_related(
        "subject", "teacher", "group"
    ).order_by("-graded_at")[:limit]