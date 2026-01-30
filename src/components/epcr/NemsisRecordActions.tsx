"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "";

interface NemsisRecordActionsProps {
  recordId: string | number;
  /** Optional state code for submit (e.g. WI). Defaults to WI. */
  stateCode?: string;
  /** Optional: show compact layout */
  compact?: boolean;
  className?: string;
}

interface SubmitResult {
  status: string;
  record_id: number;
  state_code: string;
  state_response_status?: number;
  state_response_preview?: string;
  endpoint_used?: string;
}

export function NemsisRecordActions({
  recordId,
  stateCode = "WI",
  compact = false,
  className = "",
}: NemsisRecordActionsProps) {
  const [exporting, setExporting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState<SubmitResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExportNemsis = async () => {
    setError(null);
    setExporting(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const url = `${baseUrl}/api/epcr/records/${recordId}/exports/nemsis`;
      const res = await fetch(url, {
        method: "GET",
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(res.statusText || "Export failed");
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `nemsis-record-${recordId}.xml`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export failed");
    } finally {
      setExporting(false);
    }
  };

  const handleSubmitToState = async () => {
    setError(null);
    setSubmitResult(null);
    setSubmitting(true);
    try {
      const result = await apiFetch<SubmitResult>(
        `/api/epcr/records/${recordId}/submit-to-state`,
        {
          method: "POST",
          body: JSON.stringify({ state_code: stateCode }),
        }
      );
      setSubmitResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Submit failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={`rounded-lg border border-zinc-700/80 bg-zinc-900/80 p-4 ${className}`}>
      <h3 className="text-sm font-semibold text-orange-400 mb-3">NEMSIS</h3>
      <div className={`flex flex-wrap gap-2 ${compact ? "gap-2" : "gap-3"}`}>
        <button
          type="button"
          onClick={handleExportNemsis}
          disabled={exporting}
          className="px-3 py-2 rounded-lg bg-zinc-800 text-zinc-200 hover:bg-zinc-700 text-sm font-medium disabled:opacity-50"
        >
          {exporting ? "Exporting…" : "Export NEMSIS XML"}
        </button>
        <button
          type="button"
          onClick={handleSubmitToState}
          disabled={submitting}
          className="px-3 py-2 rounded-lg bg-orange-600/20 text-orange-400 hover:bg-orange-600/30 text-sm font-medium disabled:opacity-50"
        >
          {submitting ? "Submitting…" : "Submit to state"}
        </button>
      </div>
      {error && (
        <p className="mt-2 text-sm text-red-400">{error}</p>
      )}
      {submitResult && (
        <div className="mt-3 p-2 rounded bg-zinc-800/80 text-sm">
          <span className={submitResult.status === "SUBMITTED" ? "text-green-400" : "text-amber-400"}>
            {submitResult.status}
          </span>
          {" — "}
          {submitResult.state_code}
          {submitResult.state_response_status != null && ` (HTTP ${submitResult.state_response_status})`}
          {submitResult.state_response_preview && (
            <div className="mt-1 text-zinc-500 text-xs truncate max-w-md">
              {submitResult.state_response_preview}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
