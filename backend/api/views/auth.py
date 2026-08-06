"""Autentifikatsiya, profil va foydalanuvchi boshqaruvi."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from ..audit import create_audit_log
from ..models import Notification, User
from ..roles import is_admin
from ..serializers import (
    CustomTokenObtainPairSerializer,
    UserCreateSerializer,
    UserRegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """JWT Token olish (login)."""

    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (permissions.AllowAny,)


class CustomTokenRefreshView(APIView):
    """
    JWT refresh.

    Ishni simplejwt'ning `TokenRefreshSerializer`iga topshiramiz — faqat shunda
    SIMPLE_JWT dagi ROTATE_REFRESH_TOKENS va BLACKLIST_AFTER_ROTATION haqiqatan
    ishlaydi (qo'lda yig'ilgan javob ularni jimgina chetlab o'tardi va bitta
    refresh token 7 kun davomida amal qilaverardi). O'zimizga faqat xato
    matnlari qoladi.
    """

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        if not request.data.get('refresh'):
            return Response(
                {'error': 'refresh token topilmadi'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TokenRefreshSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken):
            return Response(
                {'error': "Refresh token yaroqsiz yoki muddati tugagan"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Logout - refresh tokenni blacklist qilish."""

    # O'z hisobiga tegishli amal, ish ma'lumoti emas — nazorat roli tizimdan
    # chiqa olishi kerak.
    control_role_may_write = True

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'refresh token topilmadi'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            # Token allaqachon blacklistda yoki muddati tugagan — maqsadga
            # baribir erishilgan, shuning uchun buni xato deb hisoblamaymiz.
            # (Ilgari bu yerda `str(e)` qaytarilib, ichki xabar tashqariga
            # chiqib ketardi.)
            pass

        return Response({'message': 'Muvaffaqiyatli chiqildi'}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """Parolni o'zgartirish."""

    control_role_may_write = True

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {'error': "old_password va new_password majburiy"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        if not user.check_password(old_password):
            return Response({'error': "Eski parol noto'g'ri"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user)
        except DjangoValidationError as e:
            return Response({'new_password': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=['password'])

        create_audit_log(
            request,
            "password_changed",
            "User",
            user.id,
            {"email": user.email},
        )
        return Response({'message': "Parol muvaffaqiyatli o'zgartirildi"}, status=status.HTTP_200_OK)


class UserRegisterView(generics.CreateAPIView):
    """Ro'yxatdan o'tish."""
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = (permissions.AllowAny,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Welcome notification
        Notification.objects.create(
            user=user,
            title="E-Omborga xush kelibsiz!",
            message=f"Assalomu alaykum, {user.full_name}! E-Ombor tizimiga ro'yxatdan o'tdingiz.",
            notification_type='info'
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Muvaffaqiyatli ro\'yxatdan o\'tdingiz'
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Foydalanuvchi profili."""
    serializer_class = UserSerializer
    # Faqat o'z ismi, telefoni va shu kabilar. Rol, filial va `is_staff`
    # `UserSerializer` da read-only, ya'ni bu yerdan imtiyoz ko'tarilmaydi.
    control_role_may_write = True

    def get_object(self):
        return self.request.user


class UserListView(generics.ListCreateAPIView):
    """Foydalanuvchilar ro'yxati va yaratish (faqat admin)."""
    queryset = User.objects.select_related("branch").order_by("-created_at")

    def get_serializer_class(self):
        return UserCreateSerializer if self.request.method == "POST" else UserSerializer

    def list(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({"error": "Bu bo'limga faqat admin kira oladi"}, status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({"error": "Foydalanuvchi yaratish uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        create_audit_log(request, "user_created", "User", user.id, {"email": user.email, "roles": user.roles})
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Foydalanuvchi tafsilotlari, tahrirlash va o'chirish (faqat admin)."""
    queryset = User.objects.select_related("branch")

    def get_serializer_class(self):
        return UserUpdateSerializer if self.request.method in ("PUT", "PATCH") else UserSerializer

    def retrieve(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({"error": "Bu bo'limga faqat admin kira oladi"}, status=status.HTTP_403_FORBIDDEN)
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({"error": "Foydalanuvchini tahrirlash uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)

        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        create_audit_log(request, "user_updated", "User", user.id, {"email": user.email, "roles": user.roles})
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({"error": "Foydalanuvchini o'chirish uchun sizda ruxsat yo'q"}, status=status.HTTP_403_FORBIDDEN)

        instance = self.get_object()
        if instance.id == request.user.id:
            return Response({"error": "O'zingizni o'chira olmaysiz"}, status=status.HTTP_400_BAD_REQUEST)

        create_audit_log(request, "user_deleted", "User", instance.id, {"email": instance.email})
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
