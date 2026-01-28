"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface InspectionRecord {
  id: number;
  vehicle_id: string;
  vehicle_name: string;
  inspection_type: string;
  date: string;
  inspector: string;
  result: string;
  defects_found?: number;
  notes?: string;
  next_inspection_due?: string;
}

export default function InspectionsPage() {
  const [inspections, setInspections] = useState<InspectionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resultFilter, setResultFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    loadInspections();
  }, [resultFilter, typeFilter]);

  const loadInspections = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (resultFilter !== "all") params.append("result", resultFilter);
      if (typeFilter !== "all") params.append("type", typeFilter);

      const response = await fetch(`/api/fleet/inspections?${params.toString()}`, {
        credentials: "include"
      });
      const data = await response.json();
      setInspections(data);
      setError(null);
    } catch (err) {
      setError("Failed to load inspection records.");
    } finally {
      setLoading(false);
    }
  };

  const getResultColor = (result: string) => {
    switch (result.toLowerCase()) {
      case "pass": return "bg-green-600/20 text-green-400 border-green-600/30";
      case "fail": return "bg-red-600/20 text-red-400 border-red-600/30";
      case "conditional": return "bg-yellow-600/20 text-yellow-400 border-yellow-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  const passedInspections = inspections.filter(i => i.result.toLowerCase() === "pass").length;
  const failedInspections = inspections.filter(i => i.result.toLowerCase() === "fail").length;
  const conditionalInspections = inspections.filter(i => i.result.toLowerCase() === "conditional").length;
  const totalDefects = inspections.reduce((sum, i) => sum + (i.defects_found || 0), 0);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Vehicle Inspections</h1>
            <p className="text-zinc-400 mt-1">DVIR and inspection history</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/fleet"
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
            >
              ← Back to Fleet
            </Link>
            <Link
              href="/fleet/dvir"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              New Inspection
            </Link>
          </div>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-600/30 text-red-400 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-green-400">{passedInspections}</div>
            <div className="text-sm text-zinc-400 mt-1">Passed</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-red-400">{failedInspections}</div>
            <div className="text-sm text-zinc-400 mt-1">Failed</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-yellow-400">{conditionalInspections}</div>
            <div className="text-sm text-zinc-400 mt-1">Conditional</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-orange-400">{totalDefects}</div>
            <div className="text-sm text-zinc-400 mt-1">Total Defects</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4 mb-6">
          <div className="flex gap-4">
            <select
              value={resultFilter}
              onChange={(e) => setResultFilter(e.target.value)}
              className="bg-zinc-800 border border-zinc-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Results</option>
              <option value="pass">Pass</option>
              <option value="fail">Fail</option>
              <option value="conditional">Conditional</option>
            </select>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-zinc-800 border border-zinc-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Types</option>
              <option value="pre_trip">Pre-Trip</option>
              <option value="post_trip">Post-Trip</option>
              <option value="annual">Annual</option>
              <option value="dot">DOT</option>
            </select>
          </div>
        </div>

        {/* Inspections Table */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800">
          {loading ? (
            <div className="px-6 py-12 text-center text-zinc-400">Loading inspections...</div>
          ) : inspections.length === 0 ? (
            <div className="px-6 py-12 text-center text-zinc-400">
              No inspection records found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-zinc-800/50 text-left text-sm text-zinc-400">
                  <tr>
                    <th className="px-6 py-3">Vehicle</th>
                    <th className="px-6 py-3">Type</th>
                    <th className="px-6 py-3">Date</th>
                    <th className="px-6 py-3">Inspector</th>
                    <th className="px-6 py-3">Result</th>
                    <th className="px-6 py-3">Defects</th>
                    <th className="px-6 py-3">Next Due</th>
                    <th className="px-6 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {inspections.map((inspection) => (
                    <tr key={inspection.id} className="hover:bg-zinc-800/30 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-medium">{inspection.vehicle_name}</div>
                        <div className="text-xs text-zinc-500">{inspection.vehicle_id}</div>
                      </td>
                      <td className="px-6 py-4 text-sm">{inspection.inspection_type}</td>
                      <td className="px-6 py-4 text-sm">
                        {new Date(inspection.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-sm text-zinc-400">{inspection.inspector}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium border ${getResultColor(inspection.result)}`}>
                          {inspection.result}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {inspection.defects_found !== undefined ? (
                          <span className={inspection.defects_found > 0 ? "text-orange-400 font-medium" : "text-zinc-400"}>
                            {inspection.defects_found}
                          </span>
                        ) : (
                          "N/A"
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-zinc-400">
                        {inspection.next_inspection_due ? new Date(inspection.next_inspection_due).toLocaleDateString() : "N/A"}
                      </td>
                      <td className="px-6 py-4">
                        <button className="text-blue-400 hover:text-blue-300 text-sm">
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
