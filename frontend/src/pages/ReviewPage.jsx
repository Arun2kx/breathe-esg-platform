import toast from "react-hot-toast";
import React, { useEffect, useState, useCallback } from "react";
import {
  CheckCircle2,
  XCircle,
  Filter,
  Search,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
} from "lucide-react";
import { getRecords, reviewRecord, bulkReview } from "../lib/api";
import { StatusBadge, SuspiciousBadge, SourceBadge, ScopeBadge } from "../components/ui/Badges";
import { formatDate, formatNumber } from "../lib/utils";

const REVIEWER = "analyst";

export default function ReviewPage() {
  const [records, setRecords] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(new Set());

  // Filters
  const [filterSource, setFilterSource] = useState("");
  const [filterStatus, setFilterStatus] = useState("pending");
  const [filterSuspicious, setFilterSuspicious] = useState(false);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const fetchRecords = useCallback(() => {
    setLoading(true);
    const params = { page };
    if (filterSource) params.source = filterSource;
    if (filterStatus) params.status = filterStatus;
    if (filterSuspicious) params.suspicious = "true";
    if (search) params.search = search;

    getRecords(params)
      .then((res) => {
        setRecords(res.data.results || res.data);
        setCount(res.data.count || (res.data.results || res.data).length);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page, filterSource, filterStatus, filterSuspicious, search]);

  useEffect(() => {
    fetchRecords();
    setSelected(new Set());
  }, [fetchRecords]);

  const handleReview = async (id, status) => {
    try {
      await reviewRecord(id, { status, reviewed_by: REVIEWER });
      fetchRecords();
    } catch {}
  };

  const handleBulk = async (status) => {
  if (!selected.size) return;

  try {
    await bulkReview([...selected], status, REVIEWER);

    toast.success(`Records ${status} successfully`);

    setSelected(new Set());
    fetchRecords();
  } catch {
    toast.error("Action failed");
  }
};

  const toggleSelect = (id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === records.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(records.map((r) => r.id)));
    }
  };

  const totalPages = Math.ceil(count / 50);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-surface-900">Review Records</h1>
          <p className="mt-0.5 text-sm text-surface-500">
            {count} record{count !== 1 ? "s" : ""} matching current filters
          </p>
        </div>

        {/* Bulk actions */}
        {selected.size > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-surface-500">{selected.size} selected</span>
            <button onClick={() => handleBulk("approved")} className="btn-approve">
              <CheckCircle2 size={14} />
              Approve All
            </button>
            <button onClick={() => handleBulk("rejected")} className="btn-danger">
              <XCircle size={14} />
              Reject All
            </button>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="card mb-4 px-4 py-3 flex flex-wrap items-center gap-3">
        <Filter size={14} className="text-surface-400" />

        {/* Source filter */}
        <select
          value={filterSource}
          onChange={(e) => { setFilterSource(e.target.value); setPage(1); }}
          className="text-sm border border-surface-200 rounded px-2 py-1 text-surface-700 bg-white focus:outline-none focus:ring-1 focus:ring-esg-400"
        >
          <option value="">All Sources</option>
          <option value="sap">SAP</option>
          <option value="utility">Utility</option>
          <option value="travel">Travel</option>
        </select>

        {/* Status filter */}
        <select
          value={filterStatus}
          onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
          className="text-sm border border-surface-200 rounded px-2 py-1 text-surface-700 bg-white focus:outline-none focus:ring-1 focus:ring-esg-400"
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>

        {/* Suspicious toggle */}
        <label className="flex items-center gap-2 text-sm text-surface-600 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={filterSuspicious}
            onChange={(e) => { setFilterSuspicious(e.target.checked); setPage(1); }}
            className="rounded border-surface-300 text-esg-600"
          />
          Suspicious only
        </label>

        {/* Search */}
        <div className="ml-auto flex items-center gap-2">
          <div className="relative">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-surface-400" />
            <input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") { setSearch(searchInput); setPage(1); }
              }}
              placeholder="Search entity / site..."
              className="pl-8 pr-3 py-1 text-sm border border-surface-200 rounded bg-white text-surface-700 placeholder:text-surface-400 focus:outline-none focus:ring-1 focus:ring-esg-400 w-52"
            />
          </div>
          {(filterSource || filterStatus || filterSuspicious || search) && (
            <button
              onClick={() => {
                setFilterSource("");
                setFilterStatus("pending");
                setFilterSuspicious(false);
                setSearch("");
                setSearchInput("");
                setPage(1);
              }}
              className="text-xs text-surface-500 hover:text-surface-700 flex items-center gap-1"
            >
              <RotateCcw size={12} /> Reset
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-sm text-surface-400">Loading records…</div>
        ) : records.length === 0 ? (
          <div className="py-16 text-center text-sm text-surface-400">
            No records match the current filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="w-8">
                    <input
                      type="checkbox"
                      checked={selected.size === records.length && records.length > 0}
                      onChange={toggleAll}
                      className="rounded border-surface-300"
                    />
                  </th>
                  <th>Source</th>
                  <th>Date</th>
                  <th>Entity / Site</th>
                  <th className="text-right">Qty</th>
                  <th>Unit</th>
                  <th>Scope</th>
                  <th>Status</th>
                  <th>Flags</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id} className={r.is_suspicious ? "suspicious" : ""}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selected.has(r.id)}
                        onChange={() => toggleSelect(r.id)}
                        className="rounded border-surface-300"
                      />
                    </td>
                    <td><SourceBadge source={r.source} /></td>
                    <td className="font-mono text-xs text-surface-600">
                      {formatDate(r.activity_date)}
                    </td>
                    <td>
                      <div className="max-w-[180px]">
                        <p className="text-sm text-surface-800 truncate">{r.entity_name || "—"}</p>
                        {r.site_code && (
                          <p className="text-xs text-surface-400 font-mono truncate">{r.site_code}</p>
                        )}
                      </div>
                    </td>
                    <td className="text-right tabular-nums font-mono text-xs">
                      {r.quantity != null ? formatNumber(r.quantity) : (
                        <span className="text-surface-400">—</span>
                      )}
                    </td>
                    <td className="text-xs text-surface-500">{r.unit || "—"}</td>
                    <td><ScopeBadge scope={r.scope} /></td>
                    <td><StatusBadge status={r.status} /></td>
                    <td>
                      {r.is_suspicious ? (
                        <div className="flex flex-col gap-0.5">
                          <SuspiciousBadge />
                          {r.flag_reasons?.slice(0, 1).map((flag, i) => (
                            <span key={i} className="text-xs text-orange-600 max-w-[140px] truncate" title={flag}>
                              {flag}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-xs text-surface-400">—</span>
                      )}
                    </td>
                    <td>
                      {r.status === "pending" && (
                        <div className="flex items-center gap-1.5">
                          <button
                            onClick={() => handleReview(r.id, "approved")}
                            className="btn-approve py-1 px-2 text-xs"
                            title="Approve"
                          >
                            <CheckCircle2 size={13} />
                          </button>
                          <button
                            onClick={() => handleReview(r.id, "rejected")}
                            className="btn-danger py-1 px-2 text-xs"
                            title="Reject"
                          >
                            <XCircle size={13} />
                          </button>
                        </div>
                      )}
                      {r.status !== "pending" && (
                        <span className="text-xs text-surface-400">
                          {r.reviewed_by || "—"}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-surface-100 flex items-center justify-between">
            <span className="text-xs text-surface-500">
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary py-1 px-2 text-xs"
              >
                <ChevronLeft size={13} />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn-secondary py-1 px-2 text-xs"
              >
                <ChevronRight size={13} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
