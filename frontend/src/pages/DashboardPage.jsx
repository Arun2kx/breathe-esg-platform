import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Database,
  AlertTriangle,
  Clock,
  CheckCircle2,
  XCircle,
  Upload,
  ChevronRight,
} from "lucide-react";
import StatCard from "../components/ui/StatCard";
import { SourceBadge } from "../components/ui/Badges";
import { getStats, getBatches } from "../lib/api";
import { formatDate, formatNumber } from "../lib/utils";

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getStats(), getBatches()])
      .then(([s, b]) => {
        setStats(s.data);
        setBatches(b.data.slice(0, 8));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-surface-900">Overview</h1>
          <p className="mt-0.5 text-sm text-surface-500">
            ESG data ingestion and review status
          </p>
        </div>
        <Link to="/upload" className="btn-primary">
          <Upload size={15} />
          Upload Data
        </Link>
      </div>

      {/* KPI cards */}
      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          {Array(5).fill(0).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-3 bg-surface-200 rounded w-20 mb-3" />
              <div className="h-7 bg-surface-200 rounded w-12" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <StatCard
            label="Total Records"
            value={formatNumber(stats?.total_records, 0)}
            icon={Database}
            sub={`${formatNumber(stats?.batches, 0)} batches`}
          />
          <StatCard
            label="Pending Review"
            value={formatNumber(stats?.pending, 0)}
            icon={Clock}
            accent="text-amber-600"
          />
          <StatCard
            label="Suspicious"
            value={formatNumber(stats?.suspicious, 0)}
            icon={AlertTriangle}
            accent="text-orange-600"
            sub="Flagged for review"
          />
          <StatCard
            label="Approved"
            value={formatNumber(stats?.approved, 0)}
            icon={CheckCircle2}
            accent="text-esg-600"
          />
          <StatCard
            label="Rejected"
            value={formatNumber(stats?.rejected, 0)}
            icon={XCircle}
            accent="text-red-600"
          />
        </div>
      )}

      {/* Source breakdown */}
      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { key: "sap", label: "SAP Fuel/Procurement", scope: "Scope 1" },
            { key: "utility", label: "Utility Electricity", scope: "Scope 2" },
            { key: "travel", label: "Corporate Travel", scope: "Scope 3" },
          ].map(({ key, label, scope }) => (
            <div key={key} className="card p-4">
              <div className="flex items-center justify-between mb-3">
                <SourceBadge source={key} />
                <span className="text-xs text-surface-400">{scope}</span>
              </div>
              <p className="text-2xl font-semibold text-surface-900 tabular-nums">
                {formatNumber(stats.by_source?.[key] || 0, 0)}
              </p>
              <p className="text-xs text-surface-500 mt-0.5">records ingested</p>
            </div>
          ))}
        </div>
      )}

      {/* Recent batches */}
      <div className="card">
        <div className="px-5 py-4 border-b border-surface-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-surface-800">Recent Uploads</h2>
          <Link to="/review" className="text-xs text-esg-600 hover:text-esg-700 flex items-center gap-1">
            View all records <ChevronRight size={13} />
          </Link>
        </div>
        {batches.length === 0 ? (
          <div className="px-5 py-12 text-center">
            <Upload size={32} className="mx-auto mb-3 text-surface-300" />
            <p className="text-sm text-surface-500">No data uploaded yet.</p>
            <Link to="/upload" className="mt-3 inline-block text-sm text-esg-600 hover:underline">
              Upload your first file →
            </Link>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>File</th>
                <th>Source</th>
                <th>Uploaded</th>
                <th className="text-right">Rows</th>
                <th className="text-right">Suspicious</th>
              </tr>
            </thead>
            <tbody>
              {batches.map((b) => (
                <tr key={b.id}>
                  <td className="font-mono text-xs text-surface-600 max-w-xs truncate">
                    {b.filename}
                  </td>
                  <td><SourceBadge source={b.source} /></td>
                  <td className="text-surface-500 text-xs">{formatDate(b.uploaded_at)}</td>
                  <td className="text-right tabular-nums">{formatNumber(b.row_count, 0)}</td>
                  <td className="text-right tabular-nums">
                    {b.suspicious_count > 0 ? (
                      <span className="text-orange-600 font-medium">
                        {formatNumber(b.suspicious_count, 0)}
                      </span>
                    ) : (
                      <span className="text-surface-400">0</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
