"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import Link from "next/link";

interface PCR {
  id: string;
  incident_number: string;
  patient_name: string;
  chief_complaint: string;
  status: string;
  created_at: string;
  unit?: string;
  disposition?: string;
}

export default function PCRListPage() {
  const [pcrs, setPcrs] = useState<PCR[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    loadPCRs();
  }, [page, statusFilter]);

  const loadPCRs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: "20"
      });
      if (statusFilter !== "all") params.append("status", statusFilter);
      if (searchTerm) params.append("search", searchTerm);

      const response = await apiFetch<{ pcrs: PCR[], total_pages: number }>(
        `/api/epcr/pcrs?${params.toString()}`
      );
      setPcrs(response.pcrs || []);
      setTotalPages(response.total_pages || 1);
      setError(null);
    } catch (err) {
      setError("Failed to load PCRs.");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadPCRs();
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed": return "bg-green-600/20 text-green-400 border-green-600/30";
      case "in_progress": return "bg-yellow-600/20 text-yellow-400 border-yellow-600/30";
      case "pending": return "bg-blue-600/20 text-blue-400 border-blue-600/30";
      case "review": return "bg-purple-600/20 text-purple-400 border-purple-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Patient Care Reports</h1>
            <p className="text-zinc-400 mt-1">Search and manage all PCRs</p>
          </div>
          <Link
            href="/epcr/new"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-medium"
          >
            New PCR
          </Link>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-600/30 text-red-400 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Filters */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4 mb-6">
          <form onSubmit={handleSearch} className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by incident #, patient name, or chief complaint..."
                className="w-full bg-zinc-800 border border-zinc-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="bg-zinc-800 border border-zinc-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="review">Review</option>
            </select>
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              Search
            </button>
          </form>
        </div>

        {/* PCR Table */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800">
          {loading ? (
            <div className="px-6 py-12 text-center text-zinc-400">Loading...</div>
          ) : pcrs.length === 0 ? (
            <div className="px-6 py-12 text-center text-zinc-400">
              No PCRs found. Try adjusting your filters.
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-zinc-800/50 text-left text-sm text-zinc-400">
                    <tr>
                      <th className="px-6 py-3">Incident #</th>
                      <th className="px-6 py-3">Patient</th>
                      <th className="px-6 py-3">Chief Complaint</th>
                      <th className="px-6 py-3">Unit</th>
                      <th className="px-6 py-3">Disposition</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3">Date</th>
                      <th className="px-6 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800">
                    {pcrs.map((pcr) => (
                      <tr key={pcr.id} className="hover:bg-zinc-800/30 transition-colors">
                        <td className="px-6 py-4 font-mono text-sm">{pcr.incident_number}</td>
                        <td className="px-6 py-4">{pcr.patient_name || "Unknown"}</td>
                        <td className="px-6 py-4 text-zinc-300">{pcr.chief_complaint || "N/A"}</td>
                        <td className="px-6 py-4">
                          <span className="px-2 py-1 bg-zinc-800 rounded text-sm">
                            {pcr.unit || "N/A"}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-zinc-400">
                          {pcr.disposition || "N/A"}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(pcr.status)}`}>
                            {pcr.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-zinc-400">
                          {new Date(pcr.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4">
                          <Link
                            href={`/epcr/${pcr.id}`}
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
