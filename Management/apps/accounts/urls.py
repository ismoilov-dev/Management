from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.views import *

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    # Profile
    path("profile/", ProfileView.as_view()),
    path('settings/', UserSettingsView.as_view())

]