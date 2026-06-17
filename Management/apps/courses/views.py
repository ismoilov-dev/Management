from django.shortcuts import render
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
# local apps
from .models import Faculty, Subject, Department, Course
from apps.courses.serializers.subject import SubjectMinimalSerializer, SubjectListSerializer, SubjectDetailSerializer, SubjectWriteSerializer
from apps.courses.serializers.course import CourseMinimalSerializer, CourseListSerializer, CourseDetailSerializer, CourseWriteSerializer
from apps.courses.serializers.department import DepartmentMinimalSerializer, DepartmentListSerializer, DepartmentDetailSerializer, DepartmentWriteSerializer
from apps.courses.serializers.facility import FacultyListSerializer, FacultyWriteSerializer, FacultyDetailSerializer
from apps.core.permissions import IsSuperAdminOrAdmin



class FacultyListCreateView(generics.ListCreateAPIView):
    queryset = Faculty.objects.select_related('dean__user').prefetch_related('departments')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.request.method == "POST":
            return FacultyWriteSerializer
        return FacultyListSerializer
    
    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsSuperAdminOrAdmin()]
        return [permissions.IsAuthenticated()]

class FacultyRetrieveUpdateView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Faculty.objects.select_related('dean__user').prefetch_related('departments')
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return FacultyWriteSerializer
        return FacultyListSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAuthenticated(), IsSuperAdminOrAdmin()]
        return [permissions.IsAuthenticated()]
    
class SubjectListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course', 'semester', 'is_elective']
    search_fields    = ['name', 'code']
    ordering_fields  = ['name', 'credit_hours']
    ordering         = ['name']

    def get_queryset(self):
        if self.request.method == "GET":
            return (
                Subject.objects
                .select_related('course')        
                .prefetch_related('teachers__user')
            )
        return Subject.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SubjectWriteSerializer
        return SubjectListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsSuperAdminOrAdmin()]
        return [permissions.IsAuthenticated()]

class SubjectRetrieveUpdateView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return Subject.objects.all()  
        return (
            Subject.objects
            .select_related('course__department__faculty')
            .prefetch_related('teachers__user')
        )

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return SubjectWriteSerializer
        return SubjectDetailSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAuthenticated(), IsSuperAdminOrAdmin()]
        return [permissions.IsAuthenticated()]

class CourseListCreateView(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'level', 'is_active']
    search_fields    = ['name', 'code']
    ordering_fields  = ['name', 'price']
    ordering         = ['name']

    def get_queryset(self):
        if self.request.method == "GET":
            return (
                Course.objects
                .select_related('department__faculty')
                .prefetch_related('subjects')
            )
        return Course.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CourseWriteSerializer
        return CourseListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsSuperAdminOrAdmin()]
        return [permissions.IsAuthenticated()]

class CourseRetrieveUpdateView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return Course.objects.all()  
        return (
            Course.objects
            .select_related('department__faculty')
            .prefetch_related('subjects')
        )

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return CourseWriteSerializer
        return CourseDetailSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAuthenticated(), IsSuperAdminOrAdmin()]
        return [permissions.IsAuthenticated()]

class DepartmentListCreateView(generics.ListCreateAPIView):
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['faculty', 'is_active']
    search_fields    = ['name', 'code']
    ordering_fields  = ['name', 'created_at']
    ordering         = ['name']

    def get_queryset(self):
        if self.request.method == "GET":
            return (
                Department.objects
                .select_related('faculty', 'head__user')
                .prefetch_related('courses')
            )
        return Department.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DepartmentWriteSerializer
        return DepartmentListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsSuperAdminOrAdmin()]
        return [permissions.IsAuthenticated()]

class DepartmentRetrieveUpdateView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return Department.objects.all()  
        return (
            Department.objects
            .select_related('faculty', 'head__user')
            .prefetch_related('courses')
        )

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return DepartmentWriteSerializer
        return DepartmentDetailSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAuthenticated(), IsSuperAdminOrAdmin()]
        return [permissions.IsAuthenticated()]