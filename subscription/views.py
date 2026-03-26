from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
    OpenApiParameter
)
from drf_spectacular.types import OpenApiTypes

from .models import Tariff, Subscription
from .serializers import TariffSerializer, SubscriptionSerializer, SubscriptionCreateSerializer


class TariffListView(generics.ListAPIView):
    """
    Public endpoint to list all available tariffs.

    Returns all subscription plans that users can choose from.
    No authentication required.
    """

    queryset = Tariff.objects.all()
    serializer_class = TariffSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Получить список тарифов",
        description=(
            "Возвращает список всех доступных тарифных планов. "
            "Информация включает название, продолжительность, стоимость и статус пробного периода. "
            "Этот endpoint доступен без аутентификации."
        ),
        tags=["Tariffs"],
        responses={
            200: OpenApiResponse(
                response=TariffSerializer(many=True),
                description="Список доступных тарифных планов",
                examples=[
                    OpenApiExample(
                        "Tariffs list response",
                        summary="Список тарифов",
                        description="Пример ответа со списком тарифов",
                        value=[
                            {
                                "id": 1,
                                "title": "Базовый",
                                "days_count": 30,
                                "is_trial": False,
                                "cost": "499.00",
                                "created_at": "2026-03-01T10:00:00Z",
                                "updated_at": "2026-03-01T10:00:00Z"
                            },
                            {
                                "id": 2,
                                "title": "Премиум",
                                "days_count": 90,
                                "is_trial": False,
                                "cost": "1299.00",
                                "created_at": "2026-03-01T10:00:00Z",
                                "updated_at": "2026-03-01T10:00:00Z"
                            },
                            {
                                "id": 3,
                                "title": "Пробный",
                                "days_count": 7,
                                "is_trial": True,
                                "cost": "0.00",
                                "created_at": "2026-03-01T10:00:00Z",
                                "updated_at": "2026-03-01T10:00:00Z"
                            }
                        ],
                        response_only=True
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get list of all tariffs.

        Args:
            request: HTTP request

        Returns:
            Response: List of tariff plans
        """
        return super().list(request, *args, **kwargs)


class UserSubscriptionView(generics.RetrieveAPIView):
    """
    Authenticated endpoint to get current user's subscription.

    Returns the subscription details for the authenticated user.
    Requires JWT authentication.
    """

    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Получить подписку пользователя",
        description=(
            "Возвращает информацию о текущей подписке авторизованного пользователя. "
            "Включает детали тарифа, дату окончания и статус активности. "
            "Требуется JWT аутентификация."
        ),
        tags=["Subscription"],
        responses={
            200: OpenApiResponse(
                response=SubscriptionSerializer,
                description="Информация о подписке пользователя",
                examples=[
                    OpenApiExample(
                        "User subscription response",
                        summary="Подписка пользователя",
                        description="Пример ответа с информацией о подписке",
                        value={
                            "id": 1,
                            "tariff": 2,
                            "tariff_title": "Премиум",
                            "tariff_days_count": 90,
                            "deadline": "2026-06-10T10:00:00Z",
                            "created_at": "2026-03-12T10:00:00Z",
                            "is_active": True
                        },
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        "Unauthorized response",
                        summary="Ошибка аутентификации",
                        description="Пример ответа при отсутствии токена",
                        value={
                            "detail": "Authentication credentials were not provided."
                        },
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Подписка не найдена",
                examples=[
                    OpenApiExample(
                        "Subscription not found response",
                        summary="Подписка не найдена",
                        description="Пример ответа когда у пользователя нет подписки",
                        value={
                            "detail": "You do not have an active subscription."
                        },
                        response_only=True
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get user's subscription details.

        Args:
            request: HTTP request with authenticated user

        Returns:
            Response: Subscription details or error
        """
        return self.retrieve(request, *args, **kwargs)

    def get_object(self):
        """Get the subscription for the current authenticated user."""
        try:
            return Subscription.objects.get(user=self.request.user)
        except Subscription.DoesNotExist:
            return None

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to return 404 if user has no subscription."""
        instance = self.get_object()
        if instance is None:
            return Response(
                {'detail': 'You do not have an active subscription.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class SubscriptionCreateView(APIView):
    """
    Authenticated endpoint to create a new subscription for the current user.

    Creates a subscription using the selected tariff. User is taken from JWT token.
    User can have only one active subscription.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Create subscription for current user",
        description=(
            "Creates a subscription using selected tariff. "
            "User is taken from JWT token. "
            "User can have only one active subscription."
        ),
        tags=["Subscription"],
        request=SubscriptionCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=SubscriptionSerializer,
                description="Subscription created successfully",
                examples=[
                    OpenApiExample(
                        "Subscription created response",
                        summary="Subscription created",
                        description="Пример ответа при успешном создании подписки",
                        value={
                            "id": 1,
                            "tariff": {
                                "id": 1,
                                "title": "Premium",
                                "days_count": 30,
                                "cost": "9.99"
                            },
                            "deadline": "2026-05-12T10:00:00Z",
                            "created_at": "2026-04-12T10:00:00Z",
                            "is_active": True
                        },
                        response_only=True
                    )
                ]
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Bad request - validation error",
                examples=[
                    OpenApiExample(
                        "User already has active subscription",
                        summary="User already has active subscription",
                        description="Пример ответа когда у пользователя уже есть активная подписка",
                        value={
                            "detail": "User already has an active subscription"
                        },
                        response_only=True
                    ),
                    OpenApiExample(
                        "Invalid tariff ID",
                        summary="Invalid tariff ID",
                        description="Пример ответа при неверном ID тарифа",
                        value={
                            "tariff_id": ["Invalid pk \"999\" - object does not exist."]
                        },
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Authentication required",
                examples=[
                    OpenApiExample(
                        "Unauthorized response",
                        summary="Authentication required",
                        description="Пример ответа при отсутствии токена",
                        value={
                            "detail": "Authentication credentials were not provided."
                        },
                        response_only=True
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                "Create subscription request",
                summary="Create subscription",
                description="Пример запроса на создание подписки",
                value={
                    "tariff_id": 1
                },
                request_only=True
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new subscription for the authenticated user.

        Args:
            request: HTTP request with authenticated user and tariff_id

        Returns:
            Response: Created subscription or error
        """
        serializer = SubscriptionCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            subscription = serializer.save()
            # Return the created subscription with full details
            subscription_serializer = SubscriptionSerializer(subscription)
            return Response(
                subscription_serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
