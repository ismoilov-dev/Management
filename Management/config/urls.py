from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('attendance/', include('apps.attendance.urls')),
    path('chats/', include('apps.chats.urls')),
    path('core/', include('apps.core.urls')),
    path('courses/', include('apps.courses.urls')),
    path('grades/', include('apps.grades.urls')),
    path('groups/', include('apps.groups.urls')),
    path('homework/', include('apps.homework.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('payments/', include('apps.payments.urls')),
    path('students/', include('apps.students.urls')),
    path('tasks/', include('apps.tasks.urls')),
    path('teachers/', include('apps.teachers.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)