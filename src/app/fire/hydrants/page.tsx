"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { MapPin, Plus, Search, Droplets, AlertCircle, CheckCircle } from "lucide-react";

type Hydrant = {
  id: number;
  hydrant_number: string;
  address: string;
  latitude: number;
  longitude: number;
  hydrant_type: string;
  color: string;
  gpm_rating: number;
  last_inspection: string | null;
  next_inspection: string;
  status: string;
  condition: string;
  pressure_static: number | null;
  pressure_residual: number | null;
  notes: string;
};

export default function HydrantsPage() {
  const [hydrants, setHydrants] = useState<Hydrant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");

  useEffect(() => {
    apiFetch<Hydrant[]>("/fire/hydrants", { credentials: "include" })
      .then(setHydrants)
      .catch(() => setError("Failed to load hydrants"))
      .finally(() => setLoading(false));
  }, []);

  const filteredHydrants = hydrants.filter(hyd => {
    const matchesSearch = 
      hyd.hydrant_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      hyd.address.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === "all" || hyd.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'operational': return 'bg-green-500/20 text-green-400 border-green-500/50';
      case 'out_of_service': return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'needs_repair': return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
      default: return 'bg-zinc-700/20 text-zinc-400 border-zinc-700/50';
    }
  };

  const getFlowRateColor = (gpm: number) => {
    if (gpm >= 1500) return 'text-blue-400';
    if (gpm >= 1000) return 'text-green-400';
    if (gpm >= 500) return 'text-orange-400';
    return 'text-red-400';
  };

  const isInspectionDue = (nextInspection: string) => {
    const daysUntil = Math.floor((new Date(nextInspection).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    return daysUntil <= 30;
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="bg-gradient-to-r from-red-950 via-zinc-900 to-blue-950 border-b border-blue-900/30 px-6 py-8">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-red-500 rounded-xl">
              <Droplets className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-zinc-100">Hydrant Inventory</h1>
              <p className="text-zinc-400">Hydrant locations, inspections, and flow testing</p>
            </div>
          </div>
          <Link href="/fire/hydrants/new" className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
            <Plus className="w-5 h-5" />
            Add Hydrant
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
                placeholder="Search hydrants..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-blue-500"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="operational">Operational</option>
              <option value="out_of_service">Out of Service</option>
              <option value="needs_repair">Needs Repair</option>
            </select>
          </div>
        </motion.div>

        {loading && (
          <div className="text-center py-12">
            <Droplets className="w-12 h-12 text-blue-400 animate-pulse mx-auto mb-3" />
            <span className="text-zinc-300">Loading hydrants...</span>
          </div>
        )}

        {error && <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400">{error}</div>}

        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredHydrants.map((hyd, idx) => (
              <motion.div key={hyd.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }}>
                <Link href={`/fire/hydrants/${hyd.id}`}>
                  <div className="bg-zinc-900 border border-zinc-800 hover:border-blue-500/50 rounded-xl p-5 transition-all cursor-pointer group">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-xl font-bold text-zinc-100 group-hover:text-blue-400">{hyd.hydrant_number}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <MapPin className="w-4 h-4 text-zinc-500" />
                          <p className="text-sm text-zinc-400">{hyd.address}</p>
                        </div>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(hyd.status)}`}>
                        {hyd.status.replace('_', ' ')}
                      </span>
                    </div>

                    <div className="space-y-2 text-sm mb-3">
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Type:</span>
                        <span className="text-zinc-300">{hyd.hydrant_type}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Flow Rate:</span>
                        <span className={`font-semibold ${getFlowRateColor(hyd.gpm_rating)}`}>
                          {hyd.gpm_rating} GPM
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Color:</span>
                        <div className="flex items-center gap-2">
                          <div className={`w-4 h-4 rounded-full border border-zinc-600`} style={{ backgroundColor: hyd.color }} />
                          <span className="text-zinc-300">{hyd.color}</span>
                        </div>
                      </div>
                    </div>

                    {hyd.last_inspection && (
                      <div className="text-xs text-zinc-500 mb-2">
                        Last inspected: {new Date(hyd.last_inspection).toLocaleDateString()}
                      </div>
                    )}

                    {isInspectionDue(hyd.next_inspection) && (
                      <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/30 rounded-lg p-2">
                        <AlertCircle className="w-4 h-4" />
                        Inspection due: {new Date(hyd.next_inspection).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}

        {!loading && !error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="mt-6 bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <div className="flex items-center justify-between text-sm text-zinc-400">
              <span>Total hydrants: {hydrants.length}</span>
              <span>Due for inspection: {hydrants.filter(h => isInspectionDue(h.next_inspection)).length}</span>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
