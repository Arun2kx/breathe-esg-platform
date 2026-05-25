from django.urls import path
from review.views import RecordListView, RecordReviewView, BulkReviewView

urlpatterns = [
    path("records/", RecordListView.as_view(), name="records"),
    path("records/<int:record_id>/", RecordReviewView.as_view(), name="record-review"),
    path("bulk/", BulkReviewView.as_view(), name="bulk-review"),
]
