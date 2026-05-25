"""
Review app: analyst approve/reject workflow.

Design decision: review actions are a PATCH on the record, not a separate
endpoint. This keeps the API surface small and the state machine simple.
The audit log is written here, not in a signal, so the action is explicit.
"""

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from ingestion.models import NormalizedRecord
from ingestion.serializers import NormalizedRecordSerializer
from audit.models import AuditLog


class RecordListView(APIView):
    """
    List records with filtering. Used by the review dashboard table.
    """

    def get(self, request):
        qs = NormalizedRecord.objects.select_related("batch").all()

        # Filters
        source = request.query_params.get("source")
        status_filter = request.query_params.get("status")
        suspicious = request.query_params.get("suspicious")
        search = request.query_params.get("search")

        if source:
            qs = qs.filter(source=source)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if suspicious == "true":
            qs = qs.filter(is_suspicious=True)
        if search:
            qs = qs.filter(entity_name__icontains=search) | qs.filter(site_code__icontains=search)

        paginator = PageNumberPagination()
        paginator.page_size = 50
        page = paginator.paginate_queryset(qs, request)
        serializer = NormalizedRecordSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class RecordReviewView(APIView):
    """
    PATCH endpoint to approve or reject a single record.
    Also handles bulk operations via POST with a list of IDs.
    """

    def patch(self, request, record_id):
        try:
            record = NormalizedRecord.objects.get(pk=record_id)
        except NormalizedRecord.DoesNotExist:
            return Response({"error": "Record not found."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status")
        if new_status not in ("approved", "rejected"):
            return Response(
                {"error": "status must be 'approved' or 'rejected'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reviewed_by = request.data.get("reviewed_by", "analyst")
        note = request.data.get("note", "")

        previous_status = record.status

        record.status = new_status
        record.reviewed_by = reviewed_by
        record.reviewed_at = timezone.now()
        record.review_note = note
        record.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_note"])

        # Write audit log
        AuditLog.objects.create(
            record_id=record.id,
            batch_id=record.batch_id,
            source=record.source,
            action=new_status,
            performed_by=reviewed_by,
            note=note,
            previous_status=previous_status,
            new_status=new_status,
        )

        return Response(NormalizedRecordSerializer(record).data)


class BulkReviewView(APIView):
    """
    Approve or reject multiple records in one call.
    Used by the 'Select all + approve' flow in the dashboard.
    """

    def post(self, request):
        ids = request.data.get("ids", [])
        new_status = request.data.get("status")
        reviewed_by = request.data.get("reviewed_by", "analyst")
        note = request.data.get("note", "")

        if not ids or new_status not in ("approved", "rejected"):
            return Response({"error": "Provide ids and a valid status."}, status=400)

        records = NormalizedRecord.objects.filter(pk__in=ids)
        now = timezone.now()

        audit_entries = []
        for record in records:
            prev = record.status
            audit_entries.append(
                AuditLog(
                    record_id=record.id,
                    batch_id=record.batch_id,
                    source=record.source,
                    action=new_status,
                    performed_by=reviewed_by,
                    note=note,
                    previous_status=prev,
                    new_status=new_status,
                    timestamp=now,
                )
            )

        records.update(status=new_status, reviewed_by=reviewed_by, reviewed_at=now, review_note=note)
        AuditLog.objects.bulk_create(audit_entries)

        return Response({"updated": len(audit_entries)})
