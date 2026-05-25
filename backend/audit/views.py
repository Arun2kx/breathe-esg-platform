from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = AuditLog
        fields = "__all__"


class AuditLogView(APIView):
    def get(self, request):
        record_id = request.query_params.get("record_id")
        qs = AuditLog.objects.all()
        if record_id:
            qs = qs.filter(record_id=record_id)
        qs = qs[:100]  # cap at 100 for the dashboard
        return Response(AuditLogSerializer(qs, many=True).data)
