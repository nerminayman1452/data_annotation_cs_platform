from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("", include("django_prometheus.urls")),  # /metrics
    path("health/", include("watchman.urls")),  # health
    # path("authentication/", include("apps.user_management.urls")),  # /user authentication sys
    # proj managament system
    path("project-management/",include("apps.project_management.urls")), #project management system
    path("qualification-test/",include("apps.qualification_test.urls")), #project management system
    path("dashboard/",include("apps.dashboard.urls")), #dashboard
    path("text-annotations/",include("apps.text_annotation.urls")), #text annotation plans
    path("audio-annotations/",include("apps.audio_annotation.urls")), #audio annotation plans
    path("image-annotations/", include("apps.image_annotation.urls")),  # image annotation plans
    path("planning/", include("apps.planning.urls")),  # planning app
    path("notifications/", include("apps.notifications.urls")),  # notifications
    path("profile/", include("apps.profile.urls")),  # profile
    path("tasks/", include("apps.tasks.urls")),  # tasks
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
