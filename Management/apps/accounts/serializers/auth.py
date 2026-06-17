from rest_framework import serializers
from rest_framework.validators import UniqueValidator  
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

class RegisterSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {
                'required': True,
                'validators': [
                    UniqueValidator(
                        queryset=User.objects.all(),
                        message="Bu email manzili allaqachon ro'yxatdan o'tgan." 
                    )
                ]
            },
            'role': {'required': True}
        }
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role']
        )
        return user

class LoginSerializers(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    def validate(self, data):
        user = authenticate(email=data.get('email'), password=data.get('password'))
        if not user or not user.is_active:
            raise serializers.ValidationError("Invalid credentials or disabled account.")
        return {'user': user}

class UserMinimalSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model  = User
        fields = ["id", "first_name", "last_name", "email", "full_name"]