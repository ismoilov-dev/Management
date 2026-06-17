from django.shortcuts import render
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample
)

# local apps
from .models import StudentProfile
from .serializers import (
    StudentListSerializers,
    StudentCreateSerializer,
    StudentUpdateSerializer,
    StudentDetailSerializer
)
from apps.core.permissions import IsSuperAdminOrAdmin


@extend_schema_view(
    get=extend_schema(
        summary="Studentlar ro‘yxati",
        description="Barcha studentlarni olish",
        parameters=[
            OpenApiParameter(
                name='status',
                description='Student status filter',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='search',
                description='Search by first name, last name or email',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordering',
                description='Order by enrollment_date or user__last_name',
                required=False,
                type=str
            ),
        ]
    ),

    post=extend_schema(
        summary="Student yaratish (SuperAdmin) orqali",
        description="Yangi student profile yaratadi",
        request=StudentCreateSerializer,
        responses={201: StudentCreateSerializer},

        examples=[
            OpenApiExample(
                'Student Example',
                value={
                    "user": "31c13fb7-3fd3-471c-8368-8bd1f71301fd",
                    "date_of_birth": "2004-08-14",
                    "gender": "male",
                    "address": "Tashkent, Uzbekistan",
                    "passport": "AB1234567",
                    "enrollment_date": "2025-05-25",
                    "graduation_date": "2029-06-20",
                    "status": "active"
                },
                request_only=True
            )
        ]
    )
)
class StudentListCreateView(generics.ListCreateAPIView):

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = ['status']

    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email'
    ]

    ordering_fields = [
        'enrollment_date',
        'user__last_name'
    ]

    ordering = ['user__last_name']

    def get_queryset(self):
        if self.request.method == "GET":
            return StudentProfile.objects.select_related('user')
        return StudentProfile.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StudentCreateSerializer
        return StudentListSerializers

    def get_permissions(self):
        if self.request.method == "POST":
            return [
                permissions.IsAuthenticated(),
                IsSuperAdminOrAdmin()
            ]
        return [permissions.IsAuthenticated()]


@extend_schema_view(
    get=extend_schema(
        summary="Student detail",
        description="Bitta student ma’lumotini olish"
    ),

    put=extend_schema(
        summary="Student update",
        description="Student ma’lumotini to‘liq yangilash",
        request=StudentUpdateSerializer
    ),

    patch=extend_schema(
        summary="Student partial update",
        description="Student ma’lumotini qisman yangilash",
        request=StudentUpdateSerializer
    ),

    delete=extend_schema(
        summary="Student delete",
        description="Studentni o‘chirish"
    )
)
class StudentRetrieveUpdateDestroyAPIView(
    generics.RetrieveUpdateDestroyAPIView
):

    lookup_field = 'id'

    def get_queryset(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return StudentProfile.objects.all()

        return StudentProfile.objects.select_related('user')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return StudentUpdateSerializer

        return StudentDetailSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [
                permissions.IsAuthenticated(),
                IsSuperAdminOrAdmin()
            ]

        return [permissions.IsAuthenticated()]