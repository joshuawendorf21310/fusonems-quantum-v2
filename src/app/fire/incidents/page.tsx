"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { 
  AlertTriangle, Search, Filter, Plus, Calendar, 
  MapPin, Clock, Flame, ChevronRight 
} from "lucide-react";

type FireIncident = {
  id: number;
  incident_number: string;
  incident_type: string;
  nfirs_type: string;
  address: string;
  alarm_time: string;
  arrival_time: string | null;
  status: string;
  units_responded: number;
  property_loss: number | null;
};

export default function FireIncidentsPage() {
  const [incidents, setIncidents] = useState<FireIncident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    apiFetch<FireIncident[]>("/fire/incidents", { credentials: "include" })
      .then(setIncidents)
      .catch(() => setError("Failed to load incidents"))
      .finally(() => setLoading(false));
  }, []);

  const filteredIncidents = incidents.filter(inc => {
    const matchesSearch = 
      inc.incident_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.incident_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.address.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || inc.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'closed': return 'bg-zinc-700/20 text-zinc-400 border-zinc-700/50';
      case 'under_investigation': return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
      default: return 'bg-zinc-700/20 text-zinc-400 border-zinc-700/50';
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-950 via-zinc-900 to-orange-950 border-b border-red-900/30 px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-red-500 to-orange-500 rounded-xl">
              <AlertTriangle className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-zinc-100">Fire Incidents</h1>
              <p className="text-zinc-400">NFIRS reporting and incident management</p>
            </div>
          </div>
          <Link
            href="/fire/incidents/new"
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            <Plus className="w-5 h-5" />
            New Incident
          </Link>
        </motion.div>
      </div>

      <div className="p-6 max-w-7xl mx-auto">
        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-6"
        >
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-400" />
              <input
                type="text"
                placeholder="Search incidents..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-zinc-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-red-500"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="closed">Closed</option>
                <option value="under_investigation">Under Investigation</option>
              </select>
            </div>
          </div>
        </motion.div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-flex items-center gap-3 px-6 py-3 bg-zinc-900 rounded-full border border-zinc-800">
              <Flame className="w-5 h-5 text-red-400 animate-pulse" />
              <span className="text-zinc-300">Loading incidents...</span>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400">
            {error}
          </div>
        )}

        {/* Incidents List */}
        {!loading && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="space-y-3"
          >
            {filteredIncidents.length === 0 ? (
              <div className="text-center py-12 bg-zinc-900 border border-zinc-800 rounded-xl">
                <AlertTriangle className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                <p className="text-zinc-400">No incidents found</p>
              </div>
            ) : (
              filteredIncidents.map((incident, idx) => (
                <motion.div
                  key={incident.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                >
                  <Link href={`/fire/incidents/${incident.id}`}>
                    <div className="bg-zinc-900 border border-zinc-800 hover:border-red-500/50 rounded-xl p-5 transition-all cursor-pointer group">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-3">
                            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                            <h3 className="text-xl font-bold text-zinc-100 group-hover:text-red-400 transition-colors">
                              {incident.incident_number}
                            </h3>
                            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(incident.status)}`}>
                              {incident.status.replace('_', ' ')}
                            </span>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                            <div className="flex items-center gap-2 text-zinc-400">
                              <Flame className="w-4 h-4 text-orange-400" />
                              <span className="font-medium text-zinc-300">{incident.incident_type}</span>
                              <span className="text-zinc-500">({incident.nfirs_type})</span>
                            </div>
                            <div className="flex items-center gap-2 text-zinc-400">
                              <MapPin className="w-4 h-4" />
                              {incident.address}
                            </div>
                            <div className="flex items-center gap-2 text-zinc-400">
                              <Clock className="w-4 h-4" />
                              Alarm: {new Date(incident.alarm_time).toLocaleString()}
                            </div>
                            <div className="flex items-center gap-2 text-zinc-400">
                              <Calendar className="w-4 h-4" />
                              {incident.units_responded} units responded
                            </div>
                          </div>

                          {incident.property_loss !== null && incident.property_loss > 0 && (
                            <div className="mt-3 px-3 py-1 bg-amber-500/10 border border-amber-500/30 rounded-lg inline-block text-sm text-amber-400">
                              Property Loss: ${incident.property_loss.toLocaleString()}
                            </div>
                          )}
                        </div>

                        <ChevronRight className="w-5 h-5 text-zinc-600 group-hover:text-red-400 transition-colors flex-shrink-0 mt-1" />
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))
            )}
          </motion.div>
        )}

        {/* Summary Stats */}
        {!loading && !error && incidents.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-6 bg-zinc-900 border border-zinc-800 rounded-xl p-4"
          >
            <div className="flex items-center justify-between text-sm text-zinc-400">
              <span>Showing {filteredIncidents.length} of {incidents.length} incidents</span>
              <span>Total property loss: ${incidents.reduce((sum, inc) => sum + (inc.property_loss || 0), 0).toLocaleString()}</span>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
