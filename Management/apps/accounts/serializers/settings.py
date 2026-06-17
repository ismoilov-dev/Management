from rest_framework import serializers
from apps.accounts.models import UserSettings


class UserSettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserSettings

        fields = [
            'id',
            'language',
            'theme',
            'email_notifications',
            'sms_notifications',
            'push_notifications',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]

