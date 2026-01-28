"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { Truck, Plus, Search, AlertCircle, CheckCircle, Wrench } from "lucide-react";

type Apparatus = {
  id: number;
  unit_id: string;
  unit_name: string;
  apparatus_type: string;
  vin: string;
  year: number;
  make: string;
  model: string;
  status: string;
  mileage: number;
  next_pm_due: string | null;
  pump_test_due: string | null;
  ladder_test_due: string | null;
};

export default function ApparatusPage() {
  const [apparatus, setApparatus] = useState<Apparatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    apiFetch<Apparatus[]>("/fire/apparatus", { credentials: "include" })
      .then(setApparatus)
      .catch(() => setError("Failed to load apparatus"))
      .finally(() => setLoading(false));
  }, []);

  const filteredApparatus = apparatus.filter(app =>
    app.unit_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    app.unit_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    app.apparatus_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'in_service': return 'bg-green-500/20 text-green-400 border-green-500/50';
      case 'out_of_service': return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'maintenance': return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
      default: return 'bg-zinc-700/20 text-zinc-400 border-zinc-700/50';
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="bg-gradient-to-r from-red-950 via-zinc-900 to-orange-950 border-b border-red-900/30 px-6 py-8">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl">
              <Truck className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-zinc-100">Apparatus Management</h1>
              <p className="text-zinc-400">Fleet tracking and maintenance scheduling</p>
            </div>
          </div>
          <Link href="/fire/apparatus/new" className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg">
            <Plus className="w-5 h-5" />
            Add Apparatus
          </Link>
        </motion.div>
      </div>

      <div className="p-6 max-w-7xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
            <input
              type="text"
              placeholder="Search apparatus..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500"
            />
          </div>
        </motion.div>

        {loading && (
          <div className="text-center py-12">
            <Truck className="w-12 h-12 text-red-400 animate-pulse mx-auto mb-3" />
            <span className="text-zinc-300">Loading apparatus...</span>
          </div>
        )}

        {error && <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400">{error}</div>}

        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredApparatus.map((app, idx) => (
              <motion.div key={app.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }}>
                <Link href={`/fire/apparatus/${app.id}`}>
                  <div className="bg-zinc-900 border border-zinc-800 hover:border-red-500/50 rounded-xl p-5 transition-all cursor-pointer group">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-xl font-bold text-zinc-100 group-hover:text-red-400">{app.unit_id}</h3>
                        <p className="text-sm text-zinc-400">{app.unit_name}</p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(app.status)}`}>
                        {app.status.replace('_', ' ')}
                      </span>
                    </div>

                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2 text-zinc-400">
                        <Truck className="w-4 h-4 text-orange-400" />
                        <span className="text-zinc-300">{app.apparatus_type}</span>
                      </div>
                      <div className="text-zinc-400">
                        {app.year} {app.make} {app.model}
                      </div>
                      <div className="text-zinc-400">
                        Mileage: {app.mileage.toLocaleString()} mi
                      </div>
                    </div>

                    {app.next_pm_due && (
                      <div className="mt-3 pt-3 border-t border-zinc-800">
                        <div className="flex items-center gap-2 text-xs text-amber-400">
                          <Wrench className="w-4 h-4" />
                          PM Due: {new Date(app.next_pm_due).toLocaleDateString()}
                        </div>
                      </div>
                    )}
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
