from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiExample
from apps.accounts.serializers.auth import RegisterSerializers, LoginSerializers
from apps.accounts.serializers.profile import ProfileSerializers
from apps.accounts.serializers.settings import UserSettingsSerializer
from .models import CustomUser, UserSettings
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.permissions import IsSuperAdmin

class RegisterView(APIView):
    permission_classes = [IsSuperAdmin]
    @extend_schema(
        tags=['Accounts'],
        request=RegisterSerializers,
        responses={201: RegisterSerializers},
        description='Regitser a new user account',
        summary='Create User Acccount',
        examples=[
            OpenApiExample(
                'Valid registration Payload',
                value={'email': 'email','password': 'password', 'role': 'admin'},
                request_only=True,
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializers(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(RegisterSerializers(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    @extend_schema(
        tags=['Accounts'],
        request=LoginSerializers,
        responses={200: LoginSerializers},
        description='Login to an existing user account',
        summary='Login User Account',
        examples=[
            OpenApiExample(
                'Valid login Payload',
                value={'email': 'admin@gmail.com','password': 'adminadmin'},
                request_only=True,
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializers(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': RegisterSerializers(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# =============
# Profile
# =============

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    @extend_schema(
        tags=['Accounts'],
        responses={200: ProfileSerializers},
        description='Get the profile of the authenticated user',
        summary='User Profile',
    )
    def get(self, request, *args, **kwargs):
        serializer = ProfileSerializers(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Accounts'],
        request=ProfileSerializers,
        responses={200: ProfileSerializers},
        description='Update the profile of the authenticated user',
        summary='Update Profile',
    )
    def patch(self, request, *args, **kwargs):
        serializer = ProfileSerializers(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            user = serializer.save()
            return Response(
                ProfileSerializers(user).data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

# User Settings
class UserSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=['Accounts'],
        responses={200: UserSettingsSerializer},
        summary='Get User Settings',
        description='Get authenticated user settings',
    )
    def get(self, request):
        settings_obj, created = UserSettings.objects.get_or_create(
            user=request.user
        )
        serializer = UserSettingsSerializer(settings_obj)
        return Response(serializer.data, status=200)
    
    @extend_schema(
        tags=['Accounts'],
        request=UserSettingsSerializer,
        responses={200: UserSettingsSerializer},
        summary='Update User Settings',
        description='Update authenticated user settings',
    )
    def patch(self, request):
        settings_obj, created = UserSettings.objects.get_or_create(
            user=request.user
        )

        serializer = UserSettingsSerializer(
            settings_obj,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )