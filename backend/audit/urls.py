from django.urls import path
from audit.views import AuditLogView

urlpatterns = [
    path("logs/", AuditLogView.as_view(), name="audit-logs"),
]
