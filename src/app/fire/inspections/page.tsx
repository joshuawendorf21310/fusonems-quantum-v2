"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { ClipboardCheck, Plus, Search, AlertCircle, Calendar } from "lucide-react";

type Inspection = {
  id: number;
  inspection_number: string;
  business_name: string;
  address: string;
  inspection_type: string;
  scheduled_date: string;
  completed_date: string | null;
  status: string;
  inspector: string;
  violations: number;
  priority: string;
};

export default function InspectionsPage() {
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");

  useEffect(() => {
    apiFetch<Inspection[]>("/fire/inspections", { credentials: "include" })
      .then(setInspections)
      .catch(() => setError("Failed to load inspections"))
      .finally(() => setLoading(false));
  }, []);

  const filteredInspections = inspections.filter(ins => {
    const matchesSearch = 
      ins.business_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ins.address.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === "all" || ins.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'bg-green-500/20 text-green-400 border-green-500/50';
      case 'scheduled': return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
      case 'overdue': return 'bg-red-500/20 text-red-400 border-red-500/50';
      default: return 'bg-zinc-700/20 text-zinc-400 border-zinc-700/50';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high': return 'text-red-400';
      case 'medium': return 'text-amber-400';
      case 'low': return 'text-green-400';
      default: return 'text-zinc-400';
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="bg-gradient-to-r from-red-950 via-zinc-900 to-purple-950 border-b border-purple-900/30 px-6 py-8">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-red-500 rounded-xl">
              <ClipboardCheck className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-zinc-100">Fire Inspections</h1>
              <p className="text-zinc-400">Building and business fire safety inspections</p>
            </div>
          </div>
          <Link href="/fire/inspections/new" className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg">
            <Plus className="w-5 h-5" />
            Schedule Inspection
          </Link>
        </motion.div>
      </div>

      <div className="p-6 max-w-7xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
              <input
                type="text"
                placeholder="Search inspections..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-purple-500"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-purple-500"
            >
              <option value="all">All Status</option>
              <option value="scheduled">Scheduled</option>
              <option value="completed">Completed</option>
              <option value="overdue">Overdue</option>
            </select>
          </div>
        </motion.div>

        {loading && (
          <div className="text-center py-12">
            <ClipboardCheck className="w-12 h-12 text-purple-400 animate-pulse mx-auto mb-3" />
            <span className="text-zinc-300">Loading inspections...</span>
          </div>
        )}

        {error && <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400">{error}</div>}

        {!loading && !error && (
          <div className="space-y-3">
            {filteredInspections.map((ins, idx) => (
              <motion.div key={ins.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }}>
                <Link href={`/fire/inspections/${ins.id}`}>
                  <div className="bg-zinc-900 border border-zinc-800 hover:border-purple-500/50 rounded-xl p-5 transition-all cursor-pointer group">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-xl font-bold text-zinc-100 group-hover:text-purple-400">{ins.business_name}</h3>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(ins.status)}`}>
                            {ins.status}
                          </span>
                        </div>
                        <div className="text-sm text-zinc-400 mb-3">{ins.address}</div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                          <div>
                            <span className="text-zinc-500">Type:</span>
                            <div className="text-zinc-300">{ins.inspection_type}</div>
                          </div>
                          <div>
                            <span className="text-zinc-500">Scheduled:</span>
                            <div className="text-zinc-300">{new Date(ins.scheduled_date).toLocaleDateString()}</div>
                          </div>
                          <div>
                            <span className="text-zinc-500">Inspector:</span>
                            <div className="text-zinc-300">{ins.inspector}</div>
                          </div>
                          <div>
                            <span className="text-zinc-500">Priority:</span>
                            <div className={`font-semibold ${getPriorityColor(ins.priority)}`}>{ins.priority}</div>
                          </div>
                        </div>
                        {ins.violations > 0 && (
                          <div className="mt-3 flex items-center gap-2 text-sm text-red-400">
                            <AlertCircle className="w-4 h-4" />
                            {ins.violations} violation{ins.violations > 1 ? 's' : ''} found
                          </div>
                        )}
                      </div>
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
