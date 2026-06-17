from django.shortcuts import render
from rest_framework import generics, permissions

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiExample
)

# local apps
from .models import TeacherProfile
from apps.core.permissions import IsSuperAdminOrAdmin
from .serializers import (
    TeacherListSerializer,
    TeacherCreateSerializer,
    TeacherUpdateSerializer,
    TeacherDetailSerializer
)


@extend_schema(
    summary="Teacherlar ro‘yxati",
    description="Barcha teacherlarni olish"
)
class TeacherListView(generics.ListAPIView):

    queryset = TeacherProfile.objects.select_related(
        "user"
    ).prefetch_related(
        "subjects"
    )

    serializer_class = TeacherListSerializer

    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    summary="Teacher yaratish",
    description="Yangi teacher profile yaratish",
    request=TeacherCreateSerializer,
    responses={201: TeacherCreateSerializer},

    examples=[
        OpenApiExample(
            "Teacher Example",
            value={
                "user": "31c13fb7-3fd3-471c-8368-8bd1f71301fd",
                "date_of_birth": "1995-04-12",
                "gender": "male",
                "bio": "Python backend developer",
                "linkedin": "https://linkedin.com/in/johndoe",
                "specialization": "Backend Development",
                "degree": "Master",
                "max_weekly_hours": 20,
                "status": "active",
                "subjects": [
                    "1e9e9c53-004d-4d31-9624-6fc1cc9ed7e6"
                ]
            },
            request_only=True
        )
    ]
)
class TeacherCreateView(generics.CreateAPIView):

    queryset = TeacherProfile.objects.all()

    serializer_class = TeacherCreateSerializer

    permission_classes = [IsSuperAdminOrAdmin]


@extend_schema_view(
    get=extend_schema(
        summary="Teacher detail",
        description="Bitta teacher ma’lumotini olish"
    ),

    put=extend_schema(
        summary="Teacher update",
        description="Teacher ma’lumotini to‘liq yangilash",
        request=TeacherUpdateSerializer
    ),

    patch=extend_schema(
        summary="Teacher partial update",
        description="Teacher ma’lumotini qisman yangilash",
        request=TeacherUpdateSerializer
    ),

    delete=extend_schema(
        summary="Teacher delete",
        description="Teacherni o‘chirish"
    )
)
class TeacherRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):

    lookup_field = "id"

    def get_queryset(self):
        if self.request.method in [
            "PUT",
            "PATCH",
            "DELETE"
        ]:
            return TeacherProfile.objects.all()

        return (
            TeacherProfile.objects
            .select_related("user")
            .prefetch_related("subjects")
        )

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return TeacherUpdateSerializer

        return TeacherDetailSerializer

    def get_permissions(self):
        if self.request.method in [
            "PUT",
            "PATCH",
            "DELETE"
        ]:
            return [
                permissions.IsAuthenticated(),
                IsSuperAdminOrAdmin()
            ]

        return [permissions.IsAuthenticated()]