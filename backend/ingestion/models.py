"""
Ingestion models.

Design decisions documented in MODEL.md:
- One IngestionBatch per file upload (source tracking at the row level via FK)
- NormalizedRecord is the single canonical table all sources land in
- We store both raw and normalized values for audit/debugging purposes
- Scope is stored as a string enum (1/2/3) as per GHG Protocol categories
"""

from django.db import models
from django.utils import timezone


class IngestionBatch(models.Model):
    """
    Represents a single file upload event.
    All records ingested from that file are linked back here.
    """

    class Source(models.TextChoices):
        SAP = "sap", "SAP Fuel/Procurement"
        UTILITY = "utility", "Utility Electricity"
        TRAVEL = "travel", "Corporate Travel"

    source = models.CharField(max_length=20, choices=Source.choices)
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(default=timezone.now)
    uploaded_by = models.CharField(max_length=100, default="analyst")
    row_count = models.IntegerField(default=0)
    suspicious_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.source} – {self.filename} ({self.uploaded_at:%Y-%m-%d})"


class NormalizedRecord(models.Model):
    """
    The canonical ESG activity record after normalisation.

    All three sources collapse into this table. Source-specific fields
    that don't generalise are stored in `raw_data` (JSONField).
    This avoids a fat table with mostly-null columns.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class Scope(models.TextChoices):
        SCOPE_1 = "1", "Scope 1 – Direct emissions"
        SCOPE_2 = "2", "Scope 2 – Purchased energy"
        SCOPE_3 = "3", "Scope 3 – Value chain"

    batch = models.ForeignKey(
        IngestionBatch, on_delete=models.CASCADE, related_name="records"
    )

    # Activity identification
    source = models.CharField(max_length=20, choices=IngestionBatch.Source.choices)
    scope = models.CharField(max_length=1, choices=Scope.choices)
    activity_date = models.DateField(null=True, blank=True)

    # Normalised quantity (always in canonical unit after conversion)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    unit = models.CharField(max_length=20, blank=True)

    # Location / entity context
    site_code = models.CharField(max_length=50, blank=True)  # SAP plant code, meter ID, etc.
    entity_name = models.CharField(max_length=200, blank=True)  # Supplier name, utility, airline

    # Original raw values – kept for debugging and analyst reference
    raw_quantity = models.CharField(max_length=50, blank=True)
    raw_unit = models.CharField(max_length=50, blank=True)
    raw_date = models.CharField(max_length=50, blank=True)

    # Source-specific fields stored as JSON (avoids nullable column sprawl)
    raw_data = models.JSONField(default=dict)

    # Review state
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    is_suspicious = models.BooleanField(default=False)
    flag_reasons = models.JSONField(default=list)  # list of human-readable strings

    # Review metadata
    reviewed_by = models.CharField(max_length=100, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)

    ingested_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-ingested_at"]
        indexes = [
            models.Index(fields=["source", "status"]),
            models.Index(fields=["is_suspicious"]),
            models.Index(fields=["activity_date"]),
            models.Index(fields=["batch"]),
        ]

    def __str__(self):
        return f"{self.source} | {self.activity_date} | {self.quantity} {self.unit}"
