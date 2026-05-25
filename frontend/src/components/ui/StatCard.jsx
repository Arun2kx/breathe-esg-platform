import React from "react";
import { cn } from "../../lib/utils";

export default function StatCard({ label, value, sub, icon: Icon, accent }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-xs font-medium text-surface-500 uppercase tracking-wide">{label}</p>
          <p className={cn("mt-1.5 text-2xl font-semibold tabular-nums", accent || "text-surface-900")}>
            {value ?? "—"}
          </p>
          {sub && <p className="mt-0.5 text-xs text-surface-400">{sub}</p>}
        </div>
        {Icon && (
          <div className={cn("p-2 rounded-md", accent ? "bg-current/10" : "bg-surface-100")}>
            <Icon size={18} className={accent || "text-surface-400"} />
          </div>
        )}
      </div>
    </div>
  );
}
