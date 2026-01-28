"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { Plane, Plus, Search, Activity, AlertCircle } from "lucide-react";

type Aircraft = {
  id: number;
  tail_number: string;
  make: string;
  model: string;
  year: number;
  serial_number: string;
  status: string;
  total_hours: number;
  hours_since_inspection: number;
  next_inspection_hours: number;
  next_inspection_date: string;
  insurance_expiry: string;
  airworthiness_cert: string;
};

export default function AircraftPage() {
  const [aircraft, setAircraft] = useState<Aircraft[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<Aircraft[]>("/hems/aircraft", { credentials: "include" })
      .then(setAircraft)
      .catch(() => setError("Failed to load aircraft"))
      .finally(() => setLoading(false));
  }, []);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'operational': return 'bg-green-500/20 text-green-400 border-green-500/50';
      case 'maintenance': return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
      case 'grounded': return 'bg-red-500/20 text-red-400 border-red-500/50';
      default: return 'bg-zinc-700/20 text-zinc-400 border-zinc-700/50';
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="bg-gradient-to-r from-sky-950 via-zinc-900 to-blue-950 border-b border-sky-900/30 px-6 py-8">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-sky-500 to-blue-500 rounded-xl">
              <Plane className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-zinc-100">Aircraft Fleet</h1>
              <p className="text-zinc-400">Fleet management and specifications</p>
            </div>
          </div>
          <Link href="/hems/aircraft/new" className="flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg">
            <Plus className="w-5 h-5" />
            Add Aircraft
          </Link>
        </motion.div>
      </div>

      <div className="p-6 max-w-7xl mx-auto">
        {loading && (
          <div className="text-center py-12">
            <Plane className="w-12 h-12 text-sky-400 animate-pulse mx-auto mb-3" />
            <span className="text-zinc-300">Loading aircraft...</span>
          </div>
        )}

        {error && <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400">{error}</div>}

        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {aircraft.map((ac, idx) => (
              <motion.div key={ac.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.1 }}>
                <Link href={`/hems/aircraft/${ac.id}`}>
                  <div className="bg-zinc-900 border border-zinc-800 hover:border-sky-500/50 rounded-xl p-6 transition-all cursor-pointer group">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-2xl font-bold text-zinc-100 group-hover:text-sky-400">{ac.tail_number}</h3>
                        <p className="text-sm text-zinc-400">{ac.make} {ac.model}</p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(ac.status)}`}>
                        {ac.status}
                      </span>
                    </div>

                    <div className="space-y-2 text-sm mb-4">
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Year:</span>
                        <span className="text-zinc-300">{ac.year}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Total Hours:</span>
                        <span className="text-zinc-300">{ac.total_hours.toFixed(1)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Since Inspection:</span>
                        <span className="text-zinc-300">{ac.hours_since_inspection.toFixed(1)}</span>
                      </div>
                    </div>

                    {ac.hours_since_inspection >= ac.next_inspection_hours * 0.9 && (
                      <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/30 rounded-lg p-2">
                        <AlertCircle className="w-4 h-4" />
                        Inspection due soon
                      </div>
                    )}

                    <div className="mt-4 pt-4 border-t border-zinc-800 text-xs text-zinc-500">
                      Next inspection: {new Date(ac.next_inspection_date).toLocaleDateString()}
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
