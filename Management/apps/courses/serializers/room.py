from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.courses.models import Room


class RoomMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "building"]


class RoomListSerializer(serializers.ModelSerializer):
    room_type_display = serializers.CharField(source="get_room_type_display", read_only=True)

    class Meta:
        model = Room
        fields = [
            "id", "name", "building", "floor", 
            "capacity", "room_type", "room_type_display",
            "has_projector", "has_computer", "has_whiteboard", 
            "is_active"
        ]


class RoomDetailSerializer(serializers.ModelSerializer):
    room_type_display = serializers.CharField(source="get_room_type_display", read_only=True)

    class Meta:
        model = Room
        fields = [
            "id", "name", "building", "floor", 
            "capacity", "room_type", "room_type_display",
            "has_projector", "has_computer", "has_whiteboard", 
            "is_active", "created_at", "updated_at"
        ]


class RoomWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = [
            "name", "building", "floor", "capacity", 
            "room_type", "has_projector", "has_computer", 
            "has_whiteboard", "is_active"
        ]

    def validate_name(self, value: str) -> str:
        return value.strip()

    def validate_building(self, value: str) -> str:
        return value.strip().capitalize()

    def validate_capacity(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError(
                _("Xona sig'imi kamida 1 kishi bo'lishi kerak.")
            )
        if value > 500:
            raise serializers.ValidationError(
                _("Maksimal xona sig'imi 500 kishidan oshmasligi kerak.")
            )
        return value

    def validate_floor(self, value: int) -> int:
        if not (-5 <= value <= 50):
            raise serializers.ValidationError(
                _("Qavat raqami mantiqan to'g'ri kelmaydi (-5 va 50 orasida).")
            )
        return value

    def validate(self, attrs):

        building = attrs.get("building", getattr(self.instance, "building", None))
        name = attrs.get("name", getattr(self.instance, "name", None))

        # DB tekshiruvi
        qs = Room.objects.filter(building=building, name=name)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError({
                "name": _(f"'{building}' binosida '{name}' nomli xona allaqachon mavjud.")
            })

        return attrs