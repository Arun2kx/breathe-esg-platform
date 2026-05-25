from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ingestion.sap_ingestor import ingest_sap_csv
from ingestion.utility_ingestor import ingest_utility_csv
from ingestion.travel_ingestor import ingest_travel_csv
from ingestion.models import IngestionBatch, NormalizedRecord
from ingestion.serializers import IngestionBatchSerializer, NormalizedRecordSerializer


class UploadView(APIView):
    """
    Single upload endpoint. Source type is determined by the `source` field
    in the multipart form data, not by separate endpoints.
    This keeps the frontend simple and avoids routing logic on the client.
    """

    def post(self, request):
        source = request.data.get("source", "").lower()
        file_obj = request.FILES.get("file")

        if not file_obj:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        if source not in ("sap", "utility", "travel"):
            return Response(
                {"error": "source must be one of: sap, utility, travel"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploaded_by = request.data.get("uploaded_by", "analyst")

        try:
            if source == "sap":
                result = ingest_sap_csv(file_obj, file_obj.name, uploaded_by)
            elif source == "utility":
                result = ingest_utility_csv(file_obj, file_obj.name, uploaded_by)
            else:
                result = ingest_travel_csv(file_obj, file_obj.name, uploaded_by)
        except Exception as exc:
            return Response(
                {"error": f"Ingestion failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(result, status=status.HTTP_201_CREATED)


class BatchListView(APIView):
    def get(self, request):
        batches = IngestionBatch.objects.all()
        serializer = IngestionBatchSerializer(batches, many=True)
        return Response(serializer.data)


class StatsView(APIView):
    """Dashboard summary stats."""

    def get(self, request):
        total = NormalizedRecord.objects.count()
        suspicious = NormalizedRecord.objects.filter(is_suspicious=True).count()
        pending = NormalizedRecord.objects.filter(status="pending").count()
        approved = NormalizedRecord.objects.filter(status="approved").count()
        rejected = NormalizedRecord.objects.filter(status="rejected").count()

        by_source = {}
        for source in ("sap", "utility", "travel"):
            by_source[source] = NormalizedRecord.objects.filter(source=source).count()

        batches_count = IngestionBatch.objects.count()

        return Response({
            "total_records": total,
            "suspicious": suspicious,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "by_source": by_source,
            "batches": batches_count,
        })
