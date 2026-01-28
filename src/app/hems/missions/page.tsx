"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { Plane, Plus, Search, MapPin, Clock, Users, Activity } from "lucide-react";

type Mission = {
  id: number;
  mission_number: string;
  aircraft: string;
  tail_number: string;
  pilot: string;
  medical_crew: string[];
  departure_time: string;
  arrival_time: string | null;
  status: string;
  origin: string;
  destination: string;
  patient_name: string | null;
  flight_hours: number | null;
};

export default function MissionsPage() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");

  useEffect(() => {
    apiFetch<Mission[]>("/hems/missions", { credentials: "include" })
      .then(setMissions)
      .catch(() => setError("Failed to load missions"))
      .finally(() => setLoading(false));
  }, []);

  const filteredMissions = missions.filter(m => {
    const matchesSearch = 
      m.mission_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.aircraft.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.pilot.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === "all" || m.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'bg-sky-500/20 text-sky-400 border-sky-500/50';
      case 'completed': return 'bg-green-500/20 text-green-400 border-green-500/50';
      case 'cancelled': return 'bg-red-500/20 text-red-400 border-red-500/50';
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
              <h1 className="text-3xl font-bold text-zinc-100">Flight Missions</h1>
              <p className="text-zinc-400">HEMS mission tracking and flight logs</p>
            </div>
          </div>
          <Link href="/hems/missions/new" className="flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg">
            <Plus className="w-5 h-5" />
            New Mission
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
                placeholder="Search missions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-sky-500"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-sky-500"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </motion.div>

        {loading && (
          <div className="text-center py-12">
            <Plane className="w-12 h-12 text-sky-400 animate-pulse mx-auto mb-3" />
            <span className="text-zinc-300">Loading missions...</span>
          </div>
        )}

        {error && <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400">{error}</div>}

        {!loading && !error && (
          <div className="space-y-3">
            {filteredMissions.map((mission, idx) => (
              <motion.div key={mission.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.05 }}>
                <Link href={`/hems/missions/${mission.id}`}>
                  <div className="bg-zinc-900 border border-zinc-800 hover:border-sky-500/50 rounded-xl p-5 transition-all cursor-pointer group">
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-xl font-bold text-zinc-100 group-hover:text-sky-400">{mission.mission_number}</h3>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(mission.status)}`}>
                            {mission.status}
                          </span>
                        </div>
                        <div className="text-sm text-zinc-400">
                          {mission.aircraft} ({mission.tail_number})
                        </div>
                      </div>
                      <div className="text-right text-sm">
                        <div className="text-zinc-400">Departure</div>
                        <div className="text-zinc-200 font-semibold">{new Date(mission.departure_time).toLocaleString()}</div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div className="flex items-center gap-2 text-zinc-400">
                        <MapPin className="w-4 h-4 text-sky-400" />
                        <div>
                          <div className="text-xs text-zinc-500">Origin</div>
                          <div className="text-zinc-300">{mission.origin}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-zinc-400">
                        <MapPin className="w-4 h-4 text-green-400" />
                        <div>
                          <div className="text-xs text-zinc-500">Destination</div>
                          <div className="text-zinc-300">{mission.destination}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-zinc-400">
                        <Users className="w-4 h-4" />
                        <div>
                          <div className="text-xs text-zinc-500">Pilot</div>
                          <div className="text-zinc-300">{mission.pilot}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-zinc-400">
                        <Activity className="w-4 h-4" />
                        <div>
                          <div className="text-xs text-zinc-500">Medical Crew</div>
                          <div className="text-zinc-300">{mission.medical_crew.length}</div>
                        </div>
                      </div>
                    </div>

                    {mission.flight_hours && (
                      <div className="mt-3 pt-3 border-t border-zinc-800 text-sm text-zinc-400">
                        Flight hours: <span className="text-zinc-300 font-semibold">{mission.flight_hours.toFixed(2)}</span>
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
