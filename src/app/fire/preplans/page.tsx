"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { FileText, Plus, Search, MapPin, Building, AlertTriangle } from "lucide-react";

type PrePlan = {
  id: number;
  preplan_number: string;
  property_name: string;
  address: string;
  occupancy_type: string;
  construction_type: string;
  stories: number;
  square_footage: number;
  hazards: string[];
  water_supply: string[];
  special_considerations: string;
  last_updated: string;
  updated_by: string;
  has_hazmat: boolean;
  has_sprinklers: boolean;
  has_standpipe: boolean;
};

export default function PrePlansPage() {
  const [preplans, setPreplans] = useState<PrePlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    apiFetch<PrePlan[]>("/fire/preplans", { credentials: "include" })
      .then(setPreplans)
      .catch(() => setError("Failed to load pre-plans"))
      .finally(() => setLoading(false));
  }, []);

  const filteredPreplans = preplans.filter(pp =>
    pp.property_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    pp.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
    pp.occupancy_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="bg-gradient-to-r from-red-950 via-zinc-900 to-green-950 border-b border-green-900/30 px-6 py-8">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-green-500 to-red-500 rounded-xl">
              <FileText className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-zinc-100">Pre-Fire Plans</h1>
              <p className="text-zinc-400">Target hazard analysis and tactical pre-plans</p>
            </div>
          </div>
          <Link href="/fire/preplans/new" className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg">
            <Plus className="w-5 h-5" />
            Create Pre-Plan
          </Link>
        </motion.div>
      </div>

      <div className="p-6 max-w-7xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
            <input
              type="text"
              placeholder="Search pre-plans..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-green-500"
            />
          </div>
        </motion.div>

        {loading && (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-green-400 animate-pulse mx-auto mb-3" />
            <span className="text-zinc-300">Loading pre-plans...</span>
          </div>
        )}

        {error && <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400">{error}</div>}

        {!loading && !error && (
          <div className="space-y-4">
            {filteredPreplans.map((pp, idx) => (
              <motion.div key={pp.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }}>
                <Link href={`/fire/preplans/${pp.id}`}>
                  <div className="bg-zinc-900 border border-zinc-800 hover:border-green-500/50 rounded-xl p-6 transition-all cursor-pointer group">
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div>
                        <h3 className="text-2xl font-bold text-zinc-100 group-hover:text-green-400 mb-1">
                          {pp.property_name}
                        </h3>
                        <div className="flex items-center gap-2 text-zinc-400">
                          <MapPin className="w-4 h-4" />
                          {pp.address}
                        </div>
                      </div>
                      <div className="text-right text-sm">
                        <div className="text-zinc-500">Pre-Plan #{pp.preplan_number}</div>
                        <div className="text-zinc-400">Updated {new Date(pp.last_updated).toLocaleDateString()}</div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div>
                        <div className="text-xs text-zinc-500">Occupancy</div>
                        <div className="text-sm font-medium text-zinc-300">{pp.occupancy_type}</div>
                      </div>
                      <div>
                        <div className="text-xs text-zinc-500">Construction</div>
                        <div className="text-sm font-medium text-zinc-300">{pp.construction_type}</div>
                      </div>
                      <div>
                        <div className="text-xs text-zinc-500">Stories / Sq Ft</div>
                        <div className="text-sm font-medium text-zinc-300">
                          {pp.stories} / {pp.square_footage.toLocaleString()}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-zinc-500">Protection</div>
                        <div className="flex gap-2 mt-1">
                          {pp.has_sprinklers && (
                            <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded border border-blue-500/50">
                              Sprinklers
                            </span>
                          )}
                          {pp.has_standpipe && (
                            <span className="px-2 py-1 bg-cyan-500/20 text-cyan-400 text-xs rounded border border-cyan-500/50">
                              Standpipe
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {pp.hazards && pp.hazards.length > 0 && (
                      <div className="flex items-start gap-2 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg mb-3">
                        <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <div className="text-xs font-semibold text-amber-400 mb-1">Identified Hazards</div>
                          <div className="flex flex-wrap gap-2">
                            {pp.hazards.map((hazard, i) => (
                              <span key={i} className="px-2 py-1 bg-amber-500/20 text-amber-300 text-xs rounded">
                                {hazard}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {pp.has_hazmat && (
                      <div className="inline-flex items-center gap-2 px-3 py-1 bg-red-500/20 text-red-400 text-xs rounded-lg border border-red-500/50">
                        <AlertTriangle className="w-4 h-4" />
                        HAZMAT Present
                      </div>
                    )}

                    {pp.water_supply && pp.water_supply.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-zinc-800">
                        <div className="text-xs text-zinc-500 mb-1">Water Supply</div>
                        <div className="flex flex-wrap gap-2">
                          {pp.water_supply.map((ws, i) => (
                            <span key={i} className="px-2 py-1 bg-blue-500/10 text-blue-300 text-xs rounded border border-blue-500/30">
                              {ws}
                            </span>
                          ))}
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
