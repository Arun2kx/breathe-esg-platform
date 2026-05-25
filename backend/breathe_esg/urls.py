from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("api/ingest/", include("ingestion.urls")),
    path("api/review/", include("review.urls")),
    path("api/audit/", include("audit.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
