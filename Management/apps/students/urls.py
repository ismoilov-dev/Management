from django.urls import path
from .views import *
urlpatterns = [
    path('students/', StudentListCreateView.as_view()),
    path('students/<uuid:id>/', StudentRetrieveUpdateDestroyAPIView.as_view())
]
