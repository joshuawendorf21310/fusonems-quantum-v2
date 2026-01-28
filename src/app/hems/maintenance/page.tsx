"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { Activity, Plus, Search, AlertCircle, Wrench, Calendar } from "lucide-react";

type MaintenanceItem = {
  id: number;
  aircraft: string;
  tail_number: string;
  maintenance_type: string;
  description: string;
  scheduled_date: string;
  completed_date: string | null;
  status: string;
  technician: string | null;
  hours_at_maintenance: number;
  cost: number | null;
  next_due_hours: number | null;
  next_due_date: string | null;
};

export default function MaintenancePage() {
  const [maintenance, setMaintenance] = useState<MaintenanceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState("all");

  useEffect(() => {
    apiFetch<MaintenanceItem[]>("/hems/maintenance", { credentials: "include" })
      .then(setMaintenance)
      .catch(() => setError("Failed to load maintenance records"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = maintenance.filter(m => filterStatus === "all" || m.status === filterStatus);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'bg-green-500/20 text-green-400 border-green-500/50';
      case 'scheduled': return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
      case 'in_progress': return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
      case 'overdue': return 'bg-red-500/20 text-red-400 border-red-500/50';
      default: return 'bg-zinc-700/20 text-zinc-400 border-zinc-700/50';
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="bg-gradient-to-r from-orange-950 via-zinc-900 to-red-950 border-b border-orange-900/30 px-6 py-8">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl">
              <Wrench className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-zinc-100">Aircraft Maintenance</h1>
              <p className="text-zinc-400">Maintenance tracking and Part 135 compliance</p>
            </div>
          </div>
          <Link href="/hems/maintenance/new" className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg">
            <Plus className="w-5 h-5" />
            Log Maintenance
          </Link>
        </motion.div>
      </div>

      <div className="p-6 max-w-7xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-6">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-orange-500"
          >
            <option value="all">All Status</option>
            <option value="scheduled">Scheduled</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="overdue">Overdue</option>
          </select>
        </motion.div>

        {loading && (
          <div className="text-center py-12">
            <Wrench className="w-12 h-12 text-orange-400 animate-pulse mx-auto mb-3" />
            <span className="text-zinc-300">Loading maintenance records...</span>
          </div>
        )}

        {error && <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400">{error}</div>}

        {!loading && !error && (
          <div className="space-y-3">
            {filtered.map((item, idx) => (
              <motion.div key={item.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }}>
                <Link href={`/hems/maintenance/${item.id}`}>
                  <div className="bg-zinc-900 border border-zinc-800 hover:border-orange-500/50 rounded-xl p-5 transition-all cursor-pointer group">
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-xl font-bold text-zinc-100 group-hover:text-orange-400">
                            {item.aircraft} ({item.tail_number})
                          </h3>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(item.status)}`}>
                            {item.status.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="text-sm text-zinc-400">{item.maintenance_type}</div>
                      </div>
                      <div className="text-right text-sm">
                        <div className="text-zinc-500">Scheduled</div>
                        <div className="text-zinc-300 font-semibold">{new Date(item.scheduled_date).toLocaleDateString()}</div>
                      </div>
                    </div>

                    <div className="text-sm text-zinc-300 mb-3">{item.description}</div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                      <div>
                        <span className="text-zinc-500">Hours:</span>
                        <div className="text-zinc-300">{item.hours_at_maintenance.toFixed(1)}</div>
                      </div>
                      {item.technician && (
                        <div>
                          <span className="text-zinc-500">Technician:</span>
                          <div className="text-zinc-300">{item.technician}</div>
                        </div>
                      )}
                      {item.cost && (
                        <div>
                          <span className="text-zinc-500">Cost:</span>
                          <div className="text-zinc-300">${item.cost.toLocaleString()}</div>
                        </div>
                      )}
                      {item.next_due_date && (
                        <div>
                          <span className="text-zinc-500">Next Due:</span>
                          <div className="text-zinc-300">{new Date(item.next_due_date).toLocaleDateString()}</div>
                        </div>
                      )}
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
