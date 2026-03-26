from django.urls import path
from .views import TariffListView, UserSubscriptionView, SubscriptionCreateView

app_name = 'subscription'

urlpatterns = [
    path('tariffs/', TariffListView.as_view(), name='tariff-list'),
    path('me/', UserSubscriptionView.as_view(), name='user-subscription'),
    path('', SubscriptionCreateView.as_view(), name='subscription-create'),
]
