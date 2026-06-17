from django.shortcuts import render

# Create your views here.
from django.utils import timezone
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Task
from .serializers import (
    TaskSerializer,
    TaskCreateSerializer,
    TaskStatusUpdateSerializer,
    TaskListSerializer,
)


class TaskListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "priority", "assigned_to"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "due_date", "priority"]

    def get_queryset(self):
        return Task.objects.select_related("created_by", "assigned_to").all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TaskCreateSerializer
        return TaskListSerializer

    @extend_schema(summary="Vazifalar ro'yxati")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Yangi vazifa yaratish")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.select_related("created_by", "assigned_to").all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Vazifa detail")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Vazifani to'liq yangilash")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(summary="Vazifani qisman yangilash")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(summary="Vazifani o'chirish")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class TaskStatusUpdateView(generics.UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskStatusUpdateSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["patch"]

    @extend_schema(summary="Vazifa statusini o'zgartirish")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class MyTasksView(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "priority"]
    ordering_fields = ["due_date", "created_at"]

    def get_queryset(self):
        return Task.objects.filter(assigned_to=self.request.user).select_related("created_by")

    @extend_schema(summary="Menga biriktirilgan vazifalar")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CreatedByMeTasksView(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "priority"]

    def get_queryset(self):
        return Task.objects.filter(created_by=self.request.user).select_related("assigned_to")

    @extend_schema(summary="Men yaratgan vazifalar")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UrgentTasksView(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(
            priority=Task.Priority.URGENT,
            status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS],
        ).select_related("assigned_to", "created_by")

    @extend_schema(summary="Shoshilinch vazifalar")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class OverdueTasksView(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(
            due_date__lt=timezone.now().date(),
            status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS],
        ).select_related("assigned_to", "created_by")

    @extend_schema(summary="Muddati o'tgan vazifalar")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CompletedTasksView(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["assigned_to"]

    def get_queryset(self):
        return Task.objects.filter(status=Task.Status.DONE).select_related("assigned_to", "created_by")

    @extend_schema(summary="Bajarilgan vazifalar")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CancelledTasksView(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(status=Task.Status.CANCELLED).select_related("assigned_to")

    @extend_schema(summary="Bekor qilingan vazifalar")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TasksByPriorityView(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        priority = self.kwargs["priority"]
        return Task.objects.filter(priority=priority).select_related("assigned_to")

    @extend_schema(
        summary="Prioritet bo'yicha vazifalar",
        parameters=[OpenApiParameter("priority", str, description="low | medium | high | urgent")],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TasksByAssigneeView(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status"]

    def get_queryset(self):
        return Task.objects.filter(assigned_to_id=self.kwargs["user_id"]).select_related("assigned_to")

    @extend_schema(summary="Foydalanuvchiga biriktirilgan vazifalar")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TaskCancelView(generics.UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["patch"]

    @extend_schema(summary="Vazifani bekor qilish")
    def patch(self, request, *args, **kwargs):
        task = self.get_object()
        task.status = Task.Status.CANCELLED
        task.save(update_fields=["status"])
        return Response({"detail": "Vazifa bekor qilindi."}, status=status.HTTP_200_OK)


class TodayDueTasksView(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(
            due_date=timezone.now().date(),
            status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS],
        ).select_related("assigned_to")

    @extend_schema(summary="Bugun muddati tugaydigan vazifalar")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)