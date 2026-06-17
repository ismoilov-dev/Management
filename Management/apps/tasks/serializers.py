from rest_framework import serializers
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)

    class Meta:
        model = Task
        fields = ["id","title","description","priority","status","due_date","completed_at","created_by","created_by_name","assigned_to","assigned_to_name","created_at","updated_at",]
        read_only_fields = ["id", "created_at", "updated_at", "completed_at"]


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["title", "description", "priority", "assigned_to", "due_date"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["status"]

    def update(self, instance, validated_data):
        from django.utils import timezone
        if validated_data.get("status") == Task.Status.DONE:
            instance.completed_at = timezone.now()
        instance.status = validated_data["status"]
        instance.save()
        return instance


class TaskListSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)

    class Meta:
        model = Task
        fields = ["id", "title", "priority", "status", "due_date", "assigned_to_name"]