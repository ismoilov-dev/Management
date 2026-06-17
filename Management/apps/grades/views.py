from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Grade, SemesterGPA
from .serializers import (GradeListSerializer,GradeDetailSerializer,GradeCreateSerializer,GradeUpdateSerializer,
                          SemesterGPASerializer,SemesterGPACreateSerializer,StudentGPASummarySerializer,)
from .utils import (calculate_student_gpa_summary,get_grade_distribution,get_group_subject_statistics,
                    get_student_subject_grades,get_grades_by_type,get_recent_grades,)


# ============================================================
# UMUMIY MIXIN — Queryset filtrlash (rol asosida)
# ============================================================

class GradeQuerysetMixin:
    def get_grade_queryset(self):
        user = self.request.user
        qs   = Grade.objects.select_related(
            "student", "subject", "teacher", "group"
        ).order_by("-graded_at")

        if user.is_admin:
            return qs
        if user.is_teacher:
            return qs.filter(teacher__user=user)
        if user.is_student:
            return qs.filter(student__user=user)

        return qs.none()


# ============================================================
# GRADE VIEWS
# ============================================================

@extend_schema(
    tags=["Grades"],
    summary="Baholar ro'yxati",
    description="Barcha baholarni qaytaradi. Rol asosida avtomatik filtrlanadi.",
    parameters=[
        OpenApiParameter("student",    OpenApiTypes.UUID, description="Talaba IDsi"),
        OpenApiParameter("subject",    OpenApiTypes.UUID, description="Fan IDsi"),
        OpenApiParameter("group",      OpenApiTypes.UUID, description="Guruh IDsi"),
        OpenApiParameter("grade_type", OpenApiTypes.STR,  description="midterm | final | homework | project | quiz"),
        OpenApiParameter("search",     OpenApiTypes.STR,  description="Ism yoki fan nomi bo'yicha qidiruv"),
        OpenApiParameter("ordering",   OpenApiTypes.STR,  description="score | graded_at | grade_type"),
    ],
    responses={200: GradeListSerializer(many=True)},
)
class GradeListView(GradeQuerysetMixin, generics.ListAPIView):
    """GET /grades/ — Baholar ro'yxati."""

    serializer_class   = GradeListSerializer
    permission_classes = [IsAuthenticated]

    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        "student"   : ["exact"],
        "subject"   : ["exact"],
        "teacher"   : ["exact"],
        "group"     : ["exact"],
        "grade_type": ["exact"],
        "graded_at" : ["exact", "gte", "lte"],
        "score"     : ["gte", "lte"],
    }
    search_fields   = ["student__first_name", "student__last_name", "subject__name"]
    ordering_fields = ["score", "graded_at", "grade_type"]
    ordering        = ["-graded_at"]

    def get_queryset(self):
        return self.get_grade_queryset()


# -----------------------------------------------------------------

@extend_schema(
    tags=["Grades"],
    summary="Yangi baho qo'shish",
    description="Faqat o'qituvchi va admin baho qo'sha oladi.",
    request=GradeCreateSerializer,
    responses={201: GradeDetailSerializer},
)
class GradeCreateView(generics.CreateAPIView):
    """POST /grades/create/ — Yangi baho."""

    serializer_class   = GradeCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Faqat o'qituvchi yoki admin
        if not (request.user.is_teacher or request.user.is_admin):
            return Response(
                {"detail": "Baho qo'shish uchun o'qituvchi yoki admin bo'lish kerak."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# -----------------------------------------------------------------

@extend_schema(
    tags=["Grades"],
    summary="Bitta bahoni ko'rish",
    description="UUID bo'yicha bitta bahoning to'liq ma'lumoti.",
    responses={200: GradeDetailSerializer},
)
class GradeRetrieveView(GradeQuerysetMixin, generics.RetrieveAPIView):
    """GET /grades/<uuid:pk>/ — Bitta baho."""

    serializer_class   = GradeDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.get_grade_queryset()


# -----------------------------------------------------------------

@extend_schema(
    tags=["Grades"],
    summary="Bahoni yangilash",
    description="O'qituvchi faqat o'zi qo'ygan bahoni, admin istalganini yangilaydi.",
    request=GradeUpdateSerializer,
    responses={200: GradeDetailSerializer},
)
class GradeUpdateView(GradeQuerysetMixin, generics.UpdateAPIView):
    """PUT/PATCH /grades/<uuid:pk>/update/ — Bahoni yangilash."""

    serializer_class   = GradeUpdateSerializer
    permission_classes = [IsAuthenticated]
    http_method_names  = ["put", "patch"]

    def get_queryset(self):
        return self.get_grade_queryset()

    def update(self, request, *args, **kwargs):
        grade = self.get_object()

        # Ruxsat tekshiruvi
        if request.user.is_admin:
            pass  # Admin hamma narsani o'zgartira oladi
        elif request.user.is_teacher:
            if grade.teacher.user != request.user:
                return Response(
                    {"detail": "Siz faqat o'zingiz qo'ygan baholarni tahrirlashingiz mumkin."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            return Response(
                {"detail": "Baho tahrirlash uchun ruxsat yo'q."},
                status=status.HTTP_403_FORBIDDEN,
            )

        kwargs["partial"] = kwargs.get("partial", False)
        return super().update(request, *args, **kwargs)


# -----------------------------------------------------------------

@extend_schema(
    tags=["Grades"],
    summary="Bahoni o'chirish",
    description="Faqat admin o'chira oladi.",
    responses={204: None},
)
class GradeDestroyView(GradeQuerysetMixin, generics.DestroyAPIView):
    """DELETE /grades/<uuid:pk>/delete/ — Bahoni o'chirish."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.get_grade_queryset()

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response(
                {"detail": "Baho o'chirish faqat adminlarga ruxsat."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


# ============================================================
# GRADE — QOSHIMCHA ENDPOINT'LAR (APIView)
# ============================================================

@extend_schema(
    tags=["Grades"],
    summary="Talabaning o'z baholari",
    description="Kirgan talabaning barcha baholari. Fan yoki tur bo'yicha filtrlanadi.",
    parameters=[
        OpenApiParameter("subject",    OpenApiTypes.UUID, description="Fan IDsi"),
        OpenApiParameter("grade_type", OpenApiTypes.STR,  description="midterm | final | homework | project | quiz"),
    ],
    responses={200: GradeListSerializer(many=True)},
)
class MyGradesView(APIView):
    """GET /grades/my/ — Talabaning o'z baholari."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_student:
            return Response(
                {"detail": "Bu endpoint faqat talabalar uchun."},
                status=status.HTTP_403_FORBIDDEN,
            )

        grades = Grade.objects.filter(
            student__user=request.user,
        ).select_related("subject", "teacher", "group").order_by("-graded_at")

        # Ixtiyoriy filtrlash
        subject_id = request.query_params.get("subject")
        grade_type = request.query_params.get("grade_type")

        if subject_id:
            grades = grades.filter(subject=subject_id)
        if grade_type:
            grades = grades.filter(grade_type=grade_type)

        serializer = GradeListSerializer(grades, many=True)
        return Response(serializer.data)


# -----------------------------------------------------------------

@extend_schema(
    tags=["Grades"],
    summary="Baho turi bo'yicha baholar",
    description="Talabaning baho turi (midterm, final ...) bo'yicha filtrlangan baholari.",
    parameters=[
        OpenApiParameter("student",    OpenApiTypes.UUID, description="Talaba IDsi", required=True),
        OpenApiParameter("grade_type", OpenApiTypes.STR,  description="Baho turi",   required=True),
    ],
    responses={200: GradeListSerializer(many=True)},
)
class GradesByTypeView(APIView):
    """GET /grades/by-type/ — Tur bo'yicha baholar."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        student_id = request.query_params.get("student")
        grade_type = request.query_params.get("grade_type")

        if not student_id or not grade_type:
            return Response(
                {"detail": "student va grade_type parametrlari majburiy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Talaba faqat o'zining ID'sini yuborishi mumkin
        if request.user.is_student and str(request.user.id) != student_id:
            return Response(
                {"detail": "Siz faqat o'zingizning baholaringizni ko'rishingiz mumkin."},
                status=status.HTTP_403_FORBIDDEN,
            )

        grades     = get_grades_by_type(student_id, grade_type)
        serializer = GradeListSerializer(grades, many=True)
        return Response(serializer.data)


# -----------------------------------------------------------------

@extend_schema(
    tags=["Grades"],
    summary="So'nggi baholar",
    description="Talabaning so'nggi N ta bahosi. Dashboard uchun.",
    parameters=[
        OpenApiParameter("limit",   OpenApiTypes.INT,  description="Nechta baho (max 50, default 10)"),
        OpenApiParameter("student", OpenApiTypes.UUID, description="Admin uchun talaba IDsi"),
    ],
    responses={200: GradeListSerializer(many=True)},
)
class RecentGradesView(APIView):
    """GET /grades/recent/ — So'nggi baholar."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = min(int(request.query_params.get("limit", 10)), 50)
        except ValueError:
            limit = 10

        # Talaba o'zini, admin/teacher boshqasini so'rashi mumkin
        if request.user.is_student:
            student_id = request.user.id
        else:
            student_id = request.query_params.get("student", request.user.id)

        grades     = get_recent_grades(student_id, limit)
        serializer = GradeListSerializer(grades, many=True)
        return Response(serializer.data)


# -----------------------------------------------------------------

@extend_schema(
    tags=["Grades"],
    summary="Talabaning fandagi batafsil baholari",
    description="UUID bo'yicha baho orqali o'sha talabaning shu fandagi statistikasi.",
    responses={
        200: {
            "type": "object",
            "properties": {
                "student"      : {"type": "string"},
                "subject"      : {"type": "string"},
                "grades"       : {"type": "array"},
                "average_score": {"type": "number"},
                "total_grades" : {"type": "integer"},
                "is_passed"    : {"type": "boolean"},
                "letter_grade" : {"type": "string"},
                "gpa_point"    : {"type": "number"},
            },
        }
    },
)
class GradeSubjectDetailView(generics.RetrieveAPIView):
    """GET /grades/<uuid:pk>/subject-detail/ — Fan bo'yicha batafsil."""

    permission_classes = [IsAuthenticated]
    serializer_class   = GradeDetailSerializer  # get_object uchun kerak

    def get_queryset(self):
        return Grade.objects.select_related("student", "subject", "teacher", "group")

    def retrieve(self, request, *args, **kwargs):
        grade  = self.get_object()
        result = get_student_subject_grades(grade.student.id, grade.subject.id)

        return Response({
            "student"      : grade.student.full_name,
            "subject"      : grade.subject.name,
            "grades"       : GradeListSerializer(result["grades"], many=True).data,
            "average_score": result["average_score"],
            "total_grades" : result["total_grades"],
            "is_passed"    : result["is_passed"],
            "letter_grade" : result["letter_grade"],
            "gpa_point"    : result["gpa_point"],
        })


# ============================================================
# SEMESTER GPA VIEWS
# ============================================================

@extend_schema(
    tags=["Semester GPA"],
    summary="Semestr GPA ro'yxati",
    description="Barcha semestr GPA'larini qaytaradi. Rol asosida filtrlanadi.",
    parameters=[
        OpenApiParameter("student",  OpenApiTypes.UUID, description="Talaba IDsi"),
        OpenApiParameter("semester", OpenApiTypes.INT,  description="1 | 2 | 3"),
        OpenApiParameter("year",     OpenApiTypes.INT,  description="O'quv yili"),
    ],
    responses={200: SemesterGPASerializer(many=True)},
)
class SemesterGPAListView(generics.ListAPIView):
    """GET /semester-gpa/ — GPA ro'yxati."""

    serializer_class   = SemesterGPASerializer
    permission_classes = [IsAuthenticated]

    filter_backends  = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "student" : ["exact"],
        "semester": ["exact"],
        "year"    : ["exact", "gte", "lte"],
        "gpa"     : ["gte", "lte"],
    }
    ordering_fields = ["year", "semester", "gpa"]

    def get_queryset(self):
        user = self.request.user
        qs   = SemesterGPA.objects.select_related("student").order_by("-year", "-semester")

        if user.is_admin or user.is_teacher:
            return qs
        if user.is_student:
            return qs.filter(student__user=user)

        return qs.none()


# -----------------------------------------------------------------

@extend_schema(
    tags=["Semester GPA"],
    summary="Yangi GPA kiritish",
    description="Admin yoki tizim tomonidan manual GPA kiritish.",
    request=SemesterGPACreateSerializer,
    responses={201: SemesterGPASerializer},
)
class SemesterGPACreateView(generics.CreateAPIView):
    """POST /semester-gpa/create/ — GPA yaratish."""

    serializer_class   = SemesterGPACreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response(
                {"detail": "GPA yaratish faqat adminlarga ruxsat."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)


# -----------------------------------------------------------------

@extend_schema(
    tags=["Semester GPA"],
    summary="Bitta GPA ko'rish",
    description="UUID bo'yicha bitta semestr GPA ma'lumoti.",
    responses={200: SemesterGPASerializer},
)
class SemesterGPARetrieveView(generics.RetrieveAPIView):
    """GET /semester-gpa/<uuid:pk>/ — Bitta GPA."""

    serializer_class   = SemesterGPASerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs   = SemesterGPA.objects.select_related("student")

        if user.is_admin or user.is_teacher:
            return qs
        if user.is_student:
            return qs.filter(student__user=user)
        return qs.none()


# -----------------------------------------------------------------

@extend_schema(
    tags=["Semester GPA"],
    summary="GPA o'chirish",
    description="Faqat admin o'chira oladi.",
    responses={204: None},
)
class SemesterGPADestroyView(generics.DestroyAPIView):
    """DELETE /semester-gpa/<uuid:pk>/delete/ — GPA o'chirish."""

    permission_classes = [IsAuthenticated]
    queryset           = SemesterGPA.objects.all()

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response(
                {"detail": "GPA o'chirish faqat adminlarga ruxsat."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


# -----------------------------------------------------------------

@extend_schema(
    tags=["Semester GPA"],
    summary="Talabaning o'z GPA'lari",
    description="Kirgan talabaning barcha semestr GPA'lari.",
    responses={200: SemesterGPASerializer(many=True)},
)
class MyGPAView(APIView):
    """GET /semester-gpa/my/ — O'z GPA'larim."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_student:
            return Response(
                {"detail": "Bu endpoint faqat talabalar uchun."},
                status=status.HTTP_403_FORBIDDEN,
            )

        gpas       = SemesterGPA.objects.filter(student__user=request.user).order_by("year", "semester")
        serializer = SemesterGPASerializer(gpas, many=True)
        return Response(serializer.data)


# -----------------------------------------------------------------

@extend_schema(
    tags=["Semester GPA"],
    summary="Talabaning to'liq GPA xulosasi",
    description="Umumiy GPA, kreditlar, harf taqsimot va semestrlar bo'yicha xulosa.",
    parameters=[
        OpenApiParameter("student", OpenApiTypes.UUID, description="Talaba IDsi (admin uchun)"),
    ],
    responses={200: StudentGPASummarySerializer},
)
class GPASummaryView(APIView):
    """GET /semester-gpa/summary/ — To'liq GPA xulosasi."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Talaba o'zini, boshqalar query param orqali so'raydi
        if request.user.is_student:
            student_id = request.user.id
        else:
            student_id = request.query_params.get("student")
            if not student_id:
                return Response(
                    {"detail": "student parametri majburiy."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        summary = calculate_student_gpa_summary(student_id)

        if summary is None:
            return Response(
                {"detail": "Bu talaba uchun GPA ma'lumoti topilmadi."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StudentGPASummarySerializer(summary)
        return Response(serializer.data)


# ============================================================
# STATISTIKA VIEWS
# ============================================================

@extend_schema(
    tags=["Statistics"],
    summary="Guruh + fan statistikasi",
    description="O'qituvchi uchun guruhning bitta fan bo'yicha umumiy ko'rsatkichi.",
    parameters=[
        OpenApiParameter("group",   OpenApiTypes.UUID, description="Guruh IDsi",  required=True),
        OpenApiParameter("subject", OpenApiTypes.UUID, description="Fan IDsi",    required=True),
    ],
    responses={
        200: {
            "type": "object",
            "properties": {
                "total_grades" : {"type": "integer"},
                "average_score": {"type": "number"},
                "max_score"    : {"type": "number"},
                "min_score"    : {"type": "number"},
                "pass_count"   : {"type": "integer"},
                "fail_count"   : {"type": "integer"},
                "pass_rate"    : {"type": "number"},
                "distribution" : {"type": "object"},
                "gpa"          : {"type": "number"},
            },
        }
    },
)
class GroupSubjectStatsView(APIView):
    """GET /grades/stats/group-subject/ — Guruh va fan statistikasi."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        group_id   = request.query_params.get("group")
        subject_id = request.query_params.get("subject")

        if not group_id or not subject_id:
            return Response(
                {"detail": "group va subject parametrlari majburiy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stats = get_group_subject_statistics(group_id, subject_id)
        return Response(stats, status=status.HTTP_200_OK)


# -----------------------------------------------------------------

@extend_schema(
    tags=["Statistics"],
    summary="Talaba + fan batafsil baholari",
    description="Talabaning bitta fandagi barcha baholari va o'rtacha ko'rsatkichi.",
    parameters=[
        OpenApiParameter("student", OpenApiTypes.UUID, description="Talaba IDsi"),
        OpenApiParameter("subject", OpenApiTypes.UUID, description="Fan IDsi", required=True),
    ],
    responses={200: GradeListSerializer(many=True)},
)
class StudentSubjectGradesView(APIView):
    """GET /grades/stats/student-subject/ — Talaba va fan baholari."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_student:
            student_id = request.user.id
        else:
            student_id = request.query_params.get("student")

        subject_id = request.query_params.get("subject")

        if not student_id or not subject_id:
            return Response(
                {"detail": "student va subject parametrlari majburiy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result      = get_student_subject_grades(student_id, subject_id)
        grades_data = GradeListSerializer(result["grades"], many=True).data

        return Response({
            "grades"       : grades_data,
            "average_score": result["average_score"],
            "total_grades" : result["total_grades"],
            "is_passed"    : result["is_passed"],
            "letter_grade" : result["letter_grade"],
            "gpa_point"    : result["gpa_point"],
        }, status=status.HTTP_200_OK)


# -----------------------------------------------------------------

@extend_schema(
    tags=["Statistics"],
    summary="Harf baholar taqsimoti",
    description="Guruh yoki talaba bo'yicha A, B, C, D, F taqsimoti. Dashboard chart uchun.",
    parameters=[
        OpenApiParameter("group",   OpenApiTypes.UUID, description="Guruh IDsi"),
        OpenApiParameter("student", OpenApiTypes.UUID, description="Talaba IDsi"),
        OpenApiParameter("subject", OpenApiTypes.UUID, description="Fan IDsi (ixtiyoriy filtr)"),
    ],
    responses={
        200: {
            "type": "object",
            "properties": {
                "distribution": {
                    "type": "object",
                    "example": {"A": 5, "B": 10, "C": 8, "D": 3, "F": 2},
                },
                "total": {"type": "integer"},
            },
        }
    },
)
class GradeDistributionView(APIView):
    """GET /grades/stats/distribution/ — Harf baholar taqsimoti."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        group_id   = request.query_params.get("group")
        student_id = request.query_params.get("student")
        subject_id = request.query_params.get("subject")

        if not group_id and not student_id:
            return Response(
                {"detail": "group yoki student parametridan biri majburiy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Dinamik filter kwargs
        filter_kwargs = {}
        if group_id:
            filter_kwargs["group"]   = group_id
        if student_id:
            filter_kwargs["student"] = student_id
        if subject_id:
            filter_kwargs["subject"] = subject_id

        grades       = Grade.objects.filter(**filter_kwargs)
        distribution = get_grade_distribution(grades)

        return Response({
            "distribution": distribution,
            "total"       : sum(distribution.values()),
        }, status=status.HTTP_200_OK)