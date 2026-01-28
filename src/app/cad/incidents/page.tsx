"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import Link from "next/link";

interface Incident {
  id: string;
  incident_number: string;
  incident_type: string;
  priority: string;
  status: string;
  address: string;
  created_at: string;
  assigned_units: string[];
  closed_at?: string;
}

export default function IncidentsListPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    loadIncidents();
  }, [page, statusFilter, priorityFilter]);

  const loadIncidents = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: "20"
      });
      if (statusFilter !== "all") params.append("status", statusFilter);
      if (priorityFilter !== "all") params.append("priority", priorityFilter);

      const response = await apiFetch<{ incidents: Incident[], total_pages: number }>(
        `/api/cad/incidents?${params.toString()}`
      );
      setIncidents(response.incidents || []);
      setTotalPages(response.total_pages || 1);
      setError(null);
    } catch (err) {
      setError("Failed to load incidents.");
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case "emergency": case "high": return "bg-red-600/20 text-red-400 border-red-600/30";
      case "urgent": case "medium": return "bg-orange-600/20 text-orange-400 border-orange-600/30";
      case "low": return "bg-blue-600/20 text-blue-400 border-blue-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "dispatched": return "bg-yellow-600/20 text-yellow-400 border-yellow-600/30";
      case "en_route": return "bg-blue-600/20 text-blue-400 border-blue-600/30";
      case "on_scene": return "bg-purple-600/20 text-purple-400 border-purple-600/30";
      case "transporting": return "bg-green-600/20 text-green-400 border-green-600/30";
      case "closed": return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">CAD Incidents</h1>
            <p className="text-zinc-400 mt-1">View and manage all incidents</p>
          </div>
          <Link
            href="/cad"
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
          >
            ← Back to Dispatch Board
          </Link>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-600/30 text-red-400 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Filters */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4 mb-6">
          <div className="flex gap-4">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="bg-zinc-800 border border-zinc-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="dispatched">Dispatched</option>
              <option value="en_route">En Route</option>
              <option value="on_scene">On Scene</option>
              <option value="transporting">Transporting</option>
              <option value="closed">Closed</option>
            </select>
            <select
              value={priorityFilter}
              onChange={(e) => {
                setPriorityFilter(e.target.value);
                setPage(1);
              }}
              className="bg-zinc-800 border border-zinc-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Priorities</option>
              <option value="emergency">Emergency</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>

        {/* Incidents Table */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800">
          {loading ? (
            <div className="px-6 py-12 text-center text-zinc-400">Loading...</div>
          ) : incidents.length === 0 ? (
            <div className="px-6 py-12 text-center text-zinc-400">
              No incidents found.
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-zinc-800/50 text-left text-sm text-zinc-400">
                    <tr>
                      <th className="px-6 py-3">Incident #</th>
                      <th className="px-6 py-3">Type</th>
                      <th className="px-6 py-3">Address</th>
                      <th className="px-6 py-3">Priority</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3">Units</th>
                      <th className="px-6 py-3">Created</th>
                      <th className="px-6 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800">
                    {incidents.map((incident) => (
                      <tr key={incident.id} className="hover:bg-zinc-800/30 transition-colors">
                        <td className="px-6 py-4 font-mono text-sm">{incident.incident_number}</td>
                        <td className="px-6 py-4">{incident.incident_type}</td>
                        <td className="px-6 py-4 text-zinc-300">{incident.address}</td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded text-xs font-medium border ${getPriorityColor(incident.priority)}`}>
                            {incident.priority}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(incident.status)}`}>
                            {incident.status.replace("_", " ")}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex gap-1">
                            {incident.assigned_units.map((unit) => (
                              <span key={unit} className="px-2 py-0.5 bg-blue-600/20 text-blue-400 rounded text-xs">
                                {unit}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-zinc-400">
                          {new Date(incident.created_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4">
                          <Link
                            href={`/cad/incidents/${incident.id}`}
                            className="text-blue-400 hover:text-blue-300 text-sm"
                          >
                            View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-6 py-4 border-t border-zinc-800 flex justify-between items-center">
                  <div className="text-sm text-zinc-400">
                    Page {page} of {totalPages}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
