"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface MaintenanceRecord {
  id: number;
  vehicle_id: string;
  vehicle_name: string;
  maintenance_type: string;
  description: string;
  date: string;
  scheduled_date?: string;
  mileage?: number;
  cost?: number;
  vendor?: string;
  status: string;
}

export default function MaintenancePage() {
  const [records, setRecords] = useState<MaintenanceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    loadMaintenance();
  }, [statusFilter, typeFilter]);

  const loadMaintenance = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.append("status", statusFilter);
      if (typeFilter !== "all") params.append("type", typeFilter);

      const response = await fetch(`/api/fleet/maintenance?${params.toString()}`, {
        credentials: "include"
      });
      const data = await response.json();
      setRecords(data);
      setError(null);
    } catch (err) {
      setError("Failed to load maintenance records.");
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed": return "bg-green-600/20 text-green-400 border-green-600/30";
      case "scheduled": return "bg-blue-600/20 text-blue-400 border-blue-600/30";
      case "in_progress": return "bg-yellow-600/20 text-yellow-400 border-yellow-600/30";
      case "overdue": return "bg-red-600/20 text-red-400 border-red-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  const scheduledRecords = records.filter(r => r.status === "scheduled").length;
  const inProgressRecords = records.filter(r => r.status === "in_progress").length;
  const completedRecords = records.filter(r => r.status === "completed").length;
  const overdueRecords = records.filter(r => r.status === "overdue").length;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Fleet Maintenance</h1>
            <p className="text-zinc-400 mt-1">Scheduled and preventive maintenance</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/fleet"
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
            >
              ← Back to Fleet
            </Link>
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
              Schedule Maintenance
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-600/30 text-red-400 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-blue-400">{scheduledRecords}</div>
            <div className="text-sm text-zinc-400 mt-1">Scheduled</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-yellow-400">{inProgressRecords}</div>
            <div className="text-sm text-zinc-400 mt-1">In Progress</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-green-400">{completedRecords}</div>
            <div className="text-sm text-zinc-400 mt-1">Completed</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-red-400">{overdueRecords}</div>
            <div className="text-sm text-zinc-400 mt-1">Overdue</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4 mb-6">
          <div className="flex gap-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-zinc-800 border border-zinc-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="scheduled">Scheduled</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="overdue">Overdue</option>
            </select>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-zinc-800 border border-zinc-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Types</option>
              <option value="oil_change">Oil Change</option>
              <option value="tire_rotation">Tire Rotation</option>
              <option value="brake_service">Brake Service</option>
              <option value="inspection">Inspection</option>
              <option value="repair">Repair</option>
            </select>
          </div>
        </div>

        {/* Maintenance Table */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800">
          {loading ? (
            <div className="px-6 py-12 text-center text-zinc-400">Loading maintenance records...</div>
          ) : records.length === 0 ? (
            <div className="px-6 py-12 text-center text-zinc-400">
              No maintenance records found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-zinc-800/50 text-left text-sm text-zinc-400">
                  <tr>
                    <th className="px-6 py-3">Vehicle</th>
                    <th className="px-6 py-3">Type</th>
                    <th className="px-6 py-3">Description</th>
                    <th className="px-6 py-3">Scheduled Date</th>
                    <th className="px-6 py-3">Mileage</th>
                    <th className="px-6 py-3">Cost</th>
                    <th className="px-6 py-3">Vendor</th>
                    <th className="px-6 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {records.map((record) => (
                    <tr key={record.id} className="hover:bg-zinc-800/30 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-medium">{record.vehicle_name}</div>
                        <div className="text-xs text-zinc-500">{record.vehicle_id}</div>
                      </td>
                      <td className="px-6 py-4 text-sm">{record.maintenance_type}</td>
                      <td className="px-6 py-4 text-sm text-zinc-300">{record.description}</td>
                      <td className="px-6 py-4 text-sm">
                        {record.scheduled_date ? new Date(record.scheduled_date).toLocaleDateString() : "N/A"}
                      </td>
                      <td className="px-6 py-4 text-sm text-zinc-400">
                        {record.mileage ? `${record.mileage.toLocaleString()} mi` : "N/A"}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {record.cost ? `$${record.cost.toFixed(2)}` : "N/A"}
                      </td>
                      <td className="px-6 py-4 text-sm text-zinc-400">
                        {record.vendor || "N/A"}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(record.status)}`}>
                          {record.status}
                        </span>
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
