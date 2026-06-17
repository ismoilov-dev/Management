# apps/attendance/views.py
"""
View — bu HTTP so'rovlarni qabul qilib, javob qaytaradigan qatlam.

Bu faylda:
  1. AttendanceSessionViewSet — sessiyalar uchun CRUD + yopish action'i
  2. AttendanceRecordViewSet  — davomat yozuvlari uchun CRUD
"""

from rest_framework import viewsets ,status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import AttendanceRecord ,AttendanceSession
from .serializers import (
    AttendanceRecordSerializer,
    AttendanceSessionSerializer,
    CloseSessionSerializer,
)



# ─────────────────────────────────────────────
# 1) AttendanceSession ViewSet
# ─────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(
        summary="Sessiyalar ro'yxati",
        description="Barcha davomat sessiyalarini qaytaradi."
    ),
    create=extend_schema(
        summary="Yangi sessiya yaratish",
        description="O'qituvchi yangi dars sessiyasini ochadi."
    ),
    retrieve=extend_schema(summary="Bitta sessiyani ko'rish"),
    update=extend_schema(summary="Sessiyani to'liq yangilash"),
    partial_update=extend_schema(summary="Sessiyani qisman yangilash"),
    destroy=extend_schema(summary="Sessiyani o'chirish"),
)
class AttendanceSessionViewSet(viewsets.ModelViewSet):
    """
    Davomat sessiyalari uchun to'liq CRUD:
      GET    /sessions/          → ro'yxat
      POST   /sessions/          → yangi sessiya yaratish
      GET    /sessions/{id}/     → bitta sessiya
      PUT    /sessions/{id}/     → to'liq yangilash
      PATCH  /sessions/{id}/     → qisman yangilash
      DELETE /sessions/{id}/     → o'chirish
      POST   /sessions/{id}/close/ → sessiyani yopish (custom action)
    """
    
    # Barcha sessiyalarni olish (o'chirilmaganlarini)
    queryset = AttendanceSession.objects.select_related(
        "group","subject","teacher"
        # select_related — JOIN orqali bog'liq jadvallarni bitta so'rovda tortib oladi,
        # bu N+1 query muammosining oldini oladi.
    ).prefetch_related(
        "records_student"
        # prefetch_related — ko'p-ko'p munosabatlar uchun alohida so'rov,
        # lekin Python darajasida birlashtiradi.
    )
    
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAuthenticated]
    
    # Filtrlash, qidirish va tartiblash imkoniyatlari
    filter_backends = [
        DjangoFilterBackend,    # ?group=1&is_closed=false kabi filtrlash
        filters.SearchFilter,   # ?search=... bilan qidirish
        filters.OrderingFilter  # ?ordering=-date bilan tartiblash
    ]
    filterset_fields = ['group' , "subject" , "teacher", "date","is_closed"]
    search_fields = ['topic' , "notes"] # qidirish ishlash maydonlari
    ordering_fields = ["date" , "start_time"]
    ordering = ["-date"]   # default tartib: yangilar birinchi
    
    def get_queryset(self):
        """
        Har bir foydalanuvchi faqat o'ziga tegishli sessiyalarni ko'rsin.
        Agar o'qituvchi bo'lsa — o'zining sessiyalarini,
        admin bo'lsa — hammasini ko'radi.
        """
        user = self.request.user    
        qs = super().get_queryset()
        
        # Agar foydalanuvchi admin emas va teacher profile'i bo'lsa
        if hasattr(user, "teacher_profile") and not user.is_staff:
            qs = qs.filter(teacher=user.teacher_profile)
            
        return qs
    def perform_create(self, serializer):
        """
        Yangi sessiya yaratilganda avtomatik ravishda
        hozirgi o'qituvchini teacher maydoniga qo'yish.
        """
        # Agar foydalanuvchida teacher_profile bo'lmasa — xato chiqaradi
        teacher = getattr(self.request.user, "teacher_profile", None)
        serializer.save(teacher=teacher)
    
    # ── Custom action: sessiyani yopish ──────────────────────────────
    @extend_schema(
        summary="Sessiyani yopish",          # ← Swagger'da ko'rinadigan izoh
        description="Dars tugagach sessiyani yopadi va end_time belgilaydi.",
        request=CloseSessionSerializer,
)
    @action(
        detail=True,        # /sessions/{id}/close/  — bitta ob'ekt uchun
        methods=["post"],   # faqat POST so'rov
        url_path="close",   # URL qismi
        serializer_class =CloseSessionSerializer,
    )
    def close(self , request,pk=None):
        """
        Sessiyani yopadi va tugash vaqtini belgilaydi.
        Body: { "end_time": "14:30" }
        """
        session = self.get_object()   # URL'dagi pk bo'yicha sessiyani topadi
        
        # Agar sessiya allaqachon yopilgan bo'lsa, xato qaytaramiz
        if session.is_closed:
            return Response(
                {"detail":"Sessiya allaqachon yopilgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Kiruvchi ma'lumotlarni tekshiramiz
        serializer = CloseSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)    
        
        # Sessiyani yangilaymiz
        session.is_closed = True
        session.end_time - serializer.validated_data['end_time']
        session.save(update_fields=['is_closed', "end_time"])
        # update_fields — faqat kerakli ustunlarni yangilaydi (tezroq ishlaydi)
        
        return Response(
            {"detail":"Sessiya muvaffaqiyatli yopildi."},
            status=status.HTTP_200_OK
        )
        
        
# ─────────────────────────────────────────────
# 2) AttendanceRecord ViewSet
# ─────────────────────────────────────────────


@extend_schema_view(
    list=extend_schema(
        summary="Davomat yozuvlari ro'yxati",
        description="Barcha talabalar davomat yozuvlarini qaytaradi. "
                    "?session=1&status=absent kabi filtrlar ishlatish mumkin.",
    ),
    retrieve=extend_schema(
        summary="Bitta davomat yozuvini ko'rish",
    ),
    update=extend_schema(
        summary="Davomat yozuvini to'liq yangilash",
    ),
    destroy=extend_schema(
        summary="Davomat yozuvini o'chirish",
    ),
)
class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """
    Davomat yozuvlari uchun to'liq CRUD:
      GET    /records/          → ro'yxat
      POST   /records/          → yangi yozuv qo'shish
      GET    /records/{id}/     → bitta yozuv
      PUT    /records/{id}/     → to'liq yangilash
      PATCH  /records/{id}/     → qisman yangilash (masalan, faqat status)
      DELETE /records/{id}/     → o'chirish
    """
    
    queryset = AttendanceRecord.objects.select_related(
        "session",         # sessiya ma'lumotlari
        "student",         # talaba ma'lumotlari
    )
    
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend , filters.OrderingFilter]
    filterset_fields = ['session', 'student' , "status"] # ?session=1&status=absent
    ordering_fields = ["session__date"]
    ordering = ["-session__date"]
    
    def get_queryset(self):
        """
        URL'da ?session=<id> bo'lsa — faqat o'sha sessiyadagi record'larni qaytaradi.
        Aks holda — hammasi (filterlash keyinroq ishlaydi).
        """
        qs = super().get_queryset()
        session_id = self.request.query_params.get("session") # URL parametrini olamiz
        
        if session_id:
            qs = qs.filter(session_id=session_id)
            
        return qs
    @extend_schema(
        summary="Yangi davomat yozuvi yaratish",
        description="Bitta { ... } yoki ro'yxat [ {...}, {...} ] ko'rinishida "
                    "bir nechta talaba davomatini bir vaqtda saqlash mumkin.",
    )
    def create(self, request, *args, **kwargs):
        """
        Bir yoki bir nechta talaba davomatini bir vaqtda yaratish.
        Body: bitta ob'ekt { ... } yoki ro'yxat [ {...}, {...} ]
        """
        # Agar list (ro'yxat) kelsa — many=True bilan ishlatamiz
        is_many = isinstance(request.data, list)
        
        serializer = self.get_serializer(
            data = request.data,
            many = is_many  # True bo'lsa — ro'yxatni qabul qiladi
        )
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )
    @extend_schema(
        summary="Davomat yozuvini qisman yangilash",
        description="Faqat yuborilgan maydonlar yangilanadi. "
                    "Masalan: { \"status\": \"late\", \"minutes_late\": 10 }",
    )  
    def partial_update(self, request, *args, **kwargs):
        """
        PATCH so'rovi: faqat ayrim maydonlarni yangilash.
        Masalan, faqat status'ni o'zgartirish uchun:
          PATCH /records/5/   { "status": "late", "minutes_late": 10 }
        """
        kwargs['partial'] = True  # partial=True => barcha maydonlar shart emas
        return self.update(request, *args , **kwargs)

         