"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { Users, Plus, Search, AlertCircle, CheckCircle, Calendar } from "lucide-react";

type CrewMember = {
  id: number;
  name: string;
  role: string;
  license_number: string;
  license_expiry: string;
  medical_cert_expiry: string;
  currency_status: string;
  last_flight: string | null;
  total_hours: number;
  hours_90_days: number;
  night_currency: boolean;
  instrument_currency: boolean;
  night_vision_currency: boolean;
  training_due: string | null;
};

export default function CrewPage() {
  const [crew, setCrew] = useState<CrewMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    apiFetch<CrewMember[]>("/hems/crew", { credentials: "include" })
      .then(setCrew)
      .catch(() => setError("Failed to load crew"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = crew.filter(c =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.role.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getCurrencyColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'current': return 'bg-green-500/20 text-green-400 border-green-500/50';
      case 'expiring_soon': return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
      case 'expired': return 'bg-red-500/20 text-red-400 border-red-500/50';
      default: return 'bg-zinc-700/20 text-zinc-400 border-zinc-700/50';
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="bg-gradient-to-r from-cyan-950 via-zinc-900 to-teal-950 border-b border-cyan-900/30 px-6 py-8">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-xl">
              <Users className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-zinc-100">Flight Crew</h1>
              <p className="text-zinc-400">Pilot currency and crew management</p>
            </div>
          </div>
          <Link href="/hems/crew/new" className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg">
            <Plus className="w-5 h-5" />
            Add Crew Member
          </Link>
        </motion.div>
      </div>

      <div className="p-6 max-w-7xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
            <input
              type="text"
              placeholder="Search crew..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </motion.div>

        {loading && (
          <div className="text-center py-12">
            <Users className="w-12 h-12 text-cyan-400 animate-pulse mx-auto mb-3" />
            <span className="text-zinc-300">Loading crew...</span>
          </div>
        )}

        {error && <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400">{error}</div>}

        {!loading && !error && (
          <div className="space-y-4">
            {filtered.map((member, idx) => (
              <motion.div key={member.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }}>
                <Link href={`/hems/crew/${member.id}`}>
                  <div className="bg-zinc-900 border border-zinc-800 hover:border-cyan-500/50 rounded-xl p-6 transition-all cursor-pointer group">
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div>
                        <h3 className="text-2xl font-bold text-zinc-100 group-hover:text-cyan-400 mb-1">{member.name}</h3>
                        <div className="text-sm text-zinc-400">{member.role} - License #{member.license_number}</div>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getCurrencyColor(member.currency_status)}`}>
                        {member.currency_status.replace('_', ' ')}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div>
                        <div className="text-xs text-zinc-500">Total Hours</div>
                        <div className="text-lg font-semibold text-zinc-100">{member.total_hours.toFixed(1)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-zinc-500">90-Day Hours</div>
                        <div className="text-lg font-semibold text-zinc-100">{member.hours_90_days.toFixed(1)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-zinc-500">License Expiry</div>
                        <div className="text-sm text-zinc-300">{new Date(member.license_expiry).toLocaleDateString()}</div>
                      </div>
                      <div>
                        <div className="text-xs text-zinc-500">Medical Expiry</div>
                        <div className="text-sm text-zinc-300">{new Date(member.medical_cert_expiry).toLocaleDateString()}</div>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2 mb-3">
                      <div className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${
                        member.night_currency ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                      }`}>
                        {member.night_currency ? <CheckCircle className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                        Night Currency
                      </div>
                      <div className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${
                        member.instrument_currency ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                      }`}>
                        {member.instrument_currency ? <CheckCircle className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                        Instrument Currency
                      </div>
                      <div className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${
                        member.night_vision_currency ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                      }`}>
                        {member.night_vision_currency ? <CheckCircle className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                        NVG Currency
                      </div>
                    </div>

                    {member.training_due && (
                      <div className="flex items-center gap-2 text-sm text-amber-400 bg-amber-500/10 border border-amber-500/30 rounded-lg p-2">
                        <Calendar className="w-4 h-4" />
                        Training due: {new Date(member.training_due).toLocaleDateString()}
                      </div>
                    )}

                    {member.last_flight && (
                      <div className="mt-3 pt-3 border-t border-zinc-800 text-xs text-zinc-500">
                        Last flight: {new Date(member.last_flight).toLocaleDateString()}
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
