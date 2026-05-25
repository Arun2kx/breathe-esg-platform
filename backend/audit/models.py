from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """
    Immutable log of every state change to a NormalizedRecord.
    We never update these – only insert. Gives a clean audit trail
    suitable for presenting to auditors.
    """

    class Action(models.TextChoices):
        INGESTED = "ingested", "Ingested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        FLAGGED = "flagged", "Flagged as Suspicious"
        NOTE_ADDED = "note_added", "Note Added"

    record_id = models.IntegerField(db_index=True)
    batch_id = models.IntegerField(db_index=True)
    source = models.CharField(max_length=20)
    action = models.CharField(max_length=20, choices=Action.choices)
    performed_by = models.CharField(max_length=100, default="system")
    note = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    # Snapshot of relevant fields at time of action
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["record_id", "timestamp"])]

    def __str__(self):
        return f"{self.action} on record {self.record_id} by {self.performed_by}"
