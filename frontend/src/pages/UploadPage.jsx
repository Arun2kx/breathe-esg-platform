import React, { useState, useRef } from "react";
import { Upload, CheckCircle2, AlertTriangle, X, FileText } from "lucide-react";
import { uploadFile } from "../lib/api";
import { SourceBadge } from "../components/ui/Badges";
import { cn } from "../lib/utils";

const SOURCES = [
  {
    key: "sap",
    label: "SAP Fuel & Procurement",
    scope: "Scope 1",
    description: "IDoc flat file, ME2M / MB51 CSV export. Handles German column names and inconsistent units.",
    accepts: ".csv,.txt",
    hint: "Expected columns: Menge, MEINS, BUDAT, WERKS, LIFNR (or English equivalents)",
  },
  {
    key: "utility",
    label: "Utility Electricity",
    scope: "Scope 2",
    description: "Portal CSV export from utility providers. Handles non-calendar billing periods and mixed kWh/MWh.",
    accepts: ".csv",
    hint: "Expected columns: Meter ID, Consumption, Period Start, Location",
  },
  {
    key: "travel",
    label: "Corporate Travel",
    scope: "Scope 3",
    description: "Concur or Navan trip export. Handles flights (airport codes), hotels (nights), and ground transport.",
    accepts: ".csv",
    hint: "Expected columns: Travel Date, Type, Origin, Destination, Distance, Vendor",
  },
];

function UploadZone({ source, onSuccess }) {
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef();

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleFile = (f) => {
    setFile(f);
    setResult(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const res = await uploadFile(source.key, file);
      setResult(res.data);
      setFile(null);
      onSuccess?.();
    } catch (err) {
      setError(err.response?.data?.error || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-surface-100">
        <div className="flex items-center gap-3">
          <SourceBadge source={source.key} />
          <span className="text-xs text-surface-400">{source.scope}</span>
        </div>
        <h3 className="mt-2 text-sm font-semibold text-surface-800">{source.label}</h3>
        <p className="mt-1 text-xs text-surface-500 leading-relaxed">{source.description}</p>
      </div>

      <div className="p-5">
        {/* Result state */}
        {result && (
          <div className="mb-4 p-3 bg-esg-50 border border-esg-200 rounded-md">
            <div className="flex items-start gap-2">
              <CheckCircle2 size={15} className="text-esg-600 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-esg-800">
                <p className="font-medium">Ingestion complete</p>
                <p className="mt-0.5 text-esg-700">
                  {result.total_rows} rows processed ·{" "}
                  <span className={result.suspicious_rows > 0 ? "text-orange-600 font-medium" : ""}>
                    {result.suspicious_rows} suspicious
                  </span>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
            <AlertTriangle size={15} className="text-red-500 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-red-700">{error}</p>
          </div>
        )}

        {/* File selected */}
        {file ? (
          <div className="border border-surface-200 rounded-md px-4 py-3 flex items-center gap-3">
            <FileText size={16} className="text-surface-400 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-surface-800 font-medium truncate">{file.name}</p>
              <p className="text-xs text-surface-400">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
            <button
              onClick={() => setFile(null)}
              className="text-surface-400 hover:text-surface-600"
            >
              <X size={15} />
            </button>
          </div>
        ) : (
          /* Drop zone */
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={cn(
              "border-2 border-dashed rounded-md px-4 py-8 text-center cursor-pointer transition-colors",
              dragOver
                ? "border-esg-400 bg-esg-50"
                : "border-surface-200 hover:border-surface-300 hover:bg-surface-50"
            )}
          >
            <Upload size={20} className="mx-auto mb-2 text-surface-400" />
            <p className="text-sm text-surface-600">
              Drop CSV file here or{" "}
              <span className="text-esg-600 font-medium">browse</span>
            </p>
            <p className="mt-1 text-xs text-surface-400">{source.hint}</p>
            <input
              ref={inputRef}
              type="file"
              accept={source.accepts}
              className="hidden"
              onChange={(e) => handleFile(e.target.files[0])}
            />
          </div>
        )}

        {file && (
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="mt-3 btn-primary w-full justify-center"
          >
            {uploading ? (
              <>
                <span className="inline-block w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Upload size={14} />
                Ingest File
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

export default function UploadPage() {
  const [key, setKey] = useState(0);

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-xl font-semibold text-surface-900">Upload Data</h1>
        <p className="mt-0.5 text-sm text-surface-500">
          Ingest CSV exports from SAP, utility portals, or travel platforms. Data is normalised on upload.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {SOURCES.map((source) => (
          <UploadZone key={`${source.key}-${key}`} source={source} onSuccess={() => setKey(k => k + 1)} />
        ))}
      </div>

      {/* Notes */}
      <div className="mt-8 p-4 bg-surface-100 rounded-md border border-surface-200">
        <p className="text-xs font-semibold text-surface-600 mb-2">What happens on upload</p>
        <ul className="space-y-1 text-xs text-surface-500">
          <li>• Column names are mapped to canonical fields (handles German SAP headers)</li>
          <li>• Units are converted to a standard set: L, kWh, km, kg</li>
          <li>• Dates are parsed from all common formats including European and SAP compact</li>
          <li>• Rows with missing fields, negative quantities, or abnormal values are flagged as suspicious</li>
          <li>• All rows enter with <span className="font-medium text-amber-600">Pending</span> status — an analyst must approve before audit lock</li>
        </ul>
      </div>
    </div>
  );
}
