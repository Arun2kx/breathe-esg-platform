from django.urls import path
from ingestion.views import UploadView, BatchListView, StatsView

urlpatterns = [
    path("upload/", UploadView.as_view(), name="upload"),
    path("batches/", BatchListView.as_view(), name="batches"),
    path("stats/", StatsView.as_view(), name="stats"),
]
