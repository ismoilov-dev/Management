from django.urls import path
from .views import *
urlpatterns = [
    path('teacher-profile/', TeacherListView.as_view()),
    path('teacher-profile/create/', TeacherCreateView.as_view()),
    path('teacher-profile/<uuid:id>/', TeacherRetrieveUpdateDestroyView.as_view()),
]
