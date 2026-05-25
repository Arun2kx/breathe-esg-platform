from rest_framework import serializers
from ingestion.models import IngestionBatch, NormalizedRecord


class IngestionBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionBatch
        fields = "__all__"


class NormalizedRecordSerializer(serializers.ModelSerializer):
    batch_filename = serializers.CharField(source="batch.filename", read_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)
    scope_display = serializers.CharField(source="get_scope_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = NormalizedRecord
        fields = [
            "id", "batch", "batch_filename", "source", "source_display",
            "scope", "scope_display", "activity_date", "quantity", "unit",
            "site_code", "entity_name", "raw_quantity", "raw_unit", "raw_date",
            "status", "status_display", "is_suspicious", "flag_reasons",
            "reviewed_by", "reviewed_at", "review_note", "ingested_at",
        ]
