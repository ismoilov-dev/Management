from rest_framework import serializers
from apps.accounts.models import CustomUser
from apps.accounts.utils import upload_image_to_imgbb


class ProfileSerializers(serializers.ModelSerializer):
    avatar = serializers.ImageField(write_only=True, required=False)

    avatar_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser

        fields = [
            'id',
            'email',
            'phone',
            'first_name',
            'last_name',
            'role',
            'avatar',
            'avatar_url'
        ]

        read_only_fields = ['id', 'role', 'avatar_url']

    def get_avatar_url(self, obj) -> str | None:
        return obj.avatar

    def update(self, instance, validated_data):
        avatar = validated_data.pop('avatar', None)

        if avatar:
            image_url = upload_image_to_imgbb(avatar)

            if image_url:
                instance.avatar = image_url

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance