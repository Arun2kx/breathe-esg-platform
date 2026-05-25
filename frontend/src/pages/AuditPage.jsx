import React, { useEffect, useState } from "react";
import { ScrollText, CheckCircle2, XCircle, Upload, Flag } from "lucide-react";
import { getAuditLogs } from "../lib/api";
import { SourceBadge } from "../components/ui/Badges";
import { formatDate } from "../lib/utils";

const ACTION_ICONS = {
  ingested: { icon: Upload, cls: "text-blue-500" },
  approved: { icon: CheckCircle2, cls: "text-esg-600" },
  rejected: { icon: XCircle, cls: "text-red-500" },
  flagged: { icon: Flag, cls: "text-orange-500" },
};

export default function AuditPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAuditLogs()
      .then((res) => setLogs(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-xl font-semibold text-surface-900">Audit Log</h1>
        <p className="mt-0.5 text-sm text-surface-500">
          Immutable record of all ingestion and review actions. Suitable for auditor review.
        </p>
      </div>

      <div className="card overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-sm text-surface-400">Loading audit log…</div>
        ) : logs.length === 0 ? (
          <div className="py-16 text-center">
            <ScrollText size={32} className="mx-auto mb-3 text-surface-300" />
            <p className="text-sm text-surface-500">No audit events yet.</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Action</th>
                <th>Source</th>
                <th>Record ID</th>
                <th>Performed By</th>
                <th>Status Change</th>
                <th>Note</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => {
                const { icon: Icon, cls } = ACTION_ICONS[log.action] || ACTION_ICONS.ingested;
                return (
                  <tr key={log.id}>
                    <td className="font-mono text-xs text-surface-500 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString("en-IN", {
                        dateStyle: "medium",
                        timeStyle: "short",
                      })}
                    </td>
                    <td>
                      <span className={`flex items-center gap-1.5 text-sm font-medium ${cls}`}>
                        <Icon size={13} />
                        {log.action_display || log.action}
                      </span>
                    </td>
                    <td><SourceBadge source={log.source} /></td>
                    <td className="font-mono text-xs text-surface-500">#{log.record_id}</td>
                    <td className="text-sm text-surface-600">{log.performed_by}</td>
                    <td className="text-xs text-surface-500">
                      {log.previous_status && log.new_status ? (
                        <span>
                          <span className="text-surface-400">{log.previous_status}</span>
                          {" → "}
                          <span className="font-medium text-surface-700">{log.new_status}</span>
                        </span>
                      ) : "—"}
                    </td>
                    <td className="text-xs text-surface-500 max-w-[200px] truncate">
                      {log.note || "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
