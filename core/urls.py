from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


api = [
    path("users/", include("users.urls")),
    path("subscription/", include("subscription.urls")),
    path("courses/", include("courses.urls")),
    path("lessons/", include("lessons.urls")),
    path("quizzes/", include("quizzes.urls")),
    path("statistics/", include("quiz_statistics.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(r"^api/", include(api)),
    # Путь для скачивания самой схемы (YAML/JSON)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Красивый интерфейс Swagger
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Альтернативный интерфейс Redoc (по желанию)
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]


# urlpatterns += static(
#     settings.STATIC_URL, document_root=settings.STATIC_ROOT
# ) + static(
#     settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
# )
# Добавляем раздачу медиа-файлов только для разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
