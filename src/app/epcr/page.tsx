"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import Link from "next/link";
import { PageShell } from "@/components/PageShell";

interface PCR {
  id: string;
  incident_number: string;
  patient_name: string;
  chief_complaint: string;
  status: string;
  created_at: string;
  unit?: string;
  priority?: string;
}

interface Statistics {
  total_pcrs: number;
  pending: number;
  in_progress: number;
  completed: number;
  today: number;
}

export default function EPCRDashboard() {
  const [recentPCRs, setRecentPCRs] = useState<PCR[]>([]);
  const [stats, setStats] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      apiFetch<PCR[]>("/api/epcr/pcrs/recent").catch(() => []),
      apiFetch<Statistics>("/api/epcr/statistics").catch(() => ({
        total_pcrs: 0,
        pending: 0,
        in_progress: 0,
        completed: 0,
        today: 0
      }))
    ])
      .then(([pcrs, statistics]) => {
        setRecentPCRs(pcrs);
        setStats(statistics);
      })
      .catch(() => setError("Failed to load ePCR dashboard data."))
      .finally(() => setLoading(false));
  }, []);

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
    <PageShell title="ePCR Dashboard" requireAuth={true}>
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">ePCR Dashboard</h1>
            <p className="text-zinc-400 mt-1">Electronic Patient Care Reports</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/epcr/list"
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
            >
              View All
            </Link>
            <Link
              href="/epcr/new"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-medium"
            >
              New PCR
            </Link>
          </div>
        </div>

        {loading && (
          <div className="text-center py-12 text-zinc-400">Loading...</div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-600/30 text-red-400 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
              <div className="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
                <div className="text-3xl font-bold text-blue-400">{stats?.total_pcrs || 0}</div>
                <div className="text-sm text-zinc-400 mt-1">Total PCRs</div>
              </div>
              <div className="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
                <div className="text-3xl font-bold text-green-400">{stats?.completed || 0}</div>
                <div className="text-sm text-zinc-400 mt-1">Completed</div>
              </div>
              <div className="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
                <div className="text-3xl font-bold text-yellow-400">{stats?.in_progress || 0}</div>
                <div className="text-sm text-zinc-400 mt-1">In Progress</div>
              </div>
              <div className="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
                <div className="text-3xl font-bold text-blue-400">{stats?.pending || 0}</div>
                <div className="text-sm text-zinc-400 mt-1">Pending</div>
              </div>
              <div className="bg-zinc-900 rounded-lg p-6 border border-zinc-800">
                <div className="text-3xl font-bold text-purple-400">{stats?.today || 0}</div>
                <div className="text-sm text-zinc-400 mt-1">Today</div>
              </div>
            </div>

            <div className="bg-zinc-900 rounded-lg border border-zinc-800">
              <div className="px-6 py-4 border-b border-zinc-800">
                <h2 className="text-xl font-semibold">Recent PCRs</h2>
              </div>
              
              {recentPCRs.length === 0 ? (
                <div className="px-6 py-12 text-center text-zinc-400">
                  No recent PCRs found. Click "New PCR" to create one.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-zinc-800/50 text-left text-sm text-zinc-400">
                      <tr>
                        <th className="px-6 py-3">Incident #</th>
                        <th className="px-6 py-3">Patient</th>
                        <th className="px-6 py-3">Chief Complaint</th>
                        <th className="px-6 py-3">Unit</th>
                        <th className="px-6 py-3">Status</th>
                        <th className="px-6 py-3">Date</th>
                        <th className="px-6 py-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {recentPCRs.map((pcr) => (
                        <tr key={pcr.id} className="hover:bg-zinc-800/30 transition-colors">
                          <td className="px-6 py-4 font-mono text-sm">{pcr.incident_number}</td>
                          <td className="px-6 py-4">{pcr.patient_name || "Unknown"}</td>
                          <td className="px-6 py-4 text-zinc-300">{pcr.chief_complaint || "N/A"}</td>
                          <td className="px-6 py-4">
                            <span className="px-2 py-1 bg-zinc-800 rounded text-sm">
                              {pcr.unit || "N/A"}
                            </span>
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
              )}
            </div>
          </>
        )}
      </div>
    </PageShell>
  );
}
