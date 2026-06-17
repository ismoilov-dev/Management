from django.urls import path
from .views import *
urlpatterns = [
    path('facilty/', FacultyListCreateView.as_view()),
    path('facilty/<slug:slug>/', FacultyRetrieveUpdateView.as_view()),

    # Subject endpoints
    path('subjects/', SubjectListCreateView.as_view()),
    path('subjects/<str:slug>/', SubjectRetrieveUpdateView.as_view()),

    # Course endpoints
    path('courses/', CourseListCreateView.as_view()),
    path('courses/<str:slug>/', CourseRetrieveUpdateView.as_view()),

    # Department endpoints
    path('departments/', DepartmentListCreateView.as_view()),
    path('departments/<str:slug>/', DepartmentRetrieveUpdateView.as_view()),
]
