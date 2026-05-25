import React from "react";
import { AlertTriangle, CheckCircle2, XCircle, Clock } from "lucide-react";

export function StatusBadge({ status }) {
  const map = {
    pending: { cls: "badge-pending", icon: Clock, label: "Pending" },
    approved: { cls: "badge-approved", icon: CheckCircle2, label: "Approved" },
    rejected: { cls: "badge-rejected", icon: XCircle, label: "Rejected" },
  };
  const { cls, icon: Icon, label } = map[status] || map.pending;
  return (
    <span className={cls}>
      <Icon size={11} />
      {label}
    </span>
  );
}

export function SuspiciousBadge() {
  return (
    <span className="badge-suspicious">
      <AlertTriangle size={11} />
      Suspicious
    </span>
  );
}

export function SourceBadge({ source }) {
  const map = {
    sap: "badge-source-sap",
    utility: "badge-source-utility",
    travel: "badge-source-travel",
  };
  const labels = { sap: "SAP", utility: "Utility", travel: "Travel" };
  return <span className={map[source] || "badge-pending"}>{labels[source] || source}</span>;
}

export function ScopeBadge({ scope }) {
  const colors = {
    "1": "bg-red-50 text-red-700 border-red-200",
    "2": "bg-yellow-50 text-yellow-700 border-yellow-200",
    "3": "bg-indigo-50 text-indigo-700 border-indigo-200",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colors[scope] || ""}`}>
      Scope {scope}
    </span>
  );
}
