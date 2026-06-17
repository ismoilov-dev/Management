from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceSessionViewSet, AttendanceRecordViewSet

# ─── Router yaratamiz ────────────────────────────────────────────────
# DefaultRouter — standart REST URL'larni avtomatik generatsiya qiladi.
# trailing_slash=True bo'lsa URL oxirida / bo'ladi (default).
router = DefaultRouter()

# ViewSet'larni ro'yxatdan o'tkazamiz
# 1-argument: URL prefiksi   (masalan: "sessions" → /sessions/)
# 2-argument: ViewSet klassi
# basename:   queryset bo'lsa shart emas, lekin aniq ko'rsatgan yaxshi
router.register(
    prefix="sessions",
    viewset=AttendanceSessionViewSet,
    basename="attendance-session",
)

router.register(
    prefix="records",
    viewset=AttendanceRecordViewSet,
    basename="attendance-record",
)

# ─── URL'larni eksport qilamiz ───────────────────────────────────────
# Bu o'zgaruvchi asosiy urls.py'da include() orqali ulanadi.
urlpatterns = [
    path("", include(router.urls)),
]

