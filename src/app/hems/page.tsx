"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { 
  Plane, Activity, Users, Cloud, AlertTriangle, 
  CheckCircle, Clock, Calendar 
} from "lucide-react";
import { PageShell } from "@/components/PageShell";

type HemsDashboardData = {
  aircraft_available: number;
  pilots_current: number;
  flights_today: number;
  flight_hours_month: number;
  active_missions: Array<{
    id: number;
    mission_number: string;
    aircraft: string;
    status: string;
    departure_time: string;
    eta: string | null;
  }>;
  weather_status: string;
  maintenance_due: number;
};

const hemsModules = [
  { 
    href: "/hems/missions", 
    icon: Plane, 
    title: "Flight Missions", 
    desc: "Active and completed HEMS missions",
    color: "from-sky-600 to-blue-600"
  },
  { 
    href: "/hems/aircraft", 
    icon: Plane, 
    title: "Aircraft Fleet", 
    desc: "Fleet management and specifications",
    color: "from-blue-600 to-cyan-600"
  },
  { 
    href: "/hems/crew", 
    icon: Users, 
    title: "Flight Crew", 
    desc: "Pilot currency and crew management",
    color: "from-cyan-600 to-teal-600"
  },
  { 
    href: "/hems/weather", 
    icon: Cloud, 
    title: "Weather", 
    desc: "Weather minimums and decision log",
    color: "from-teal-600 to-emerald-600"
  },
  { 
    href: "/hems/frat", 
    icon: AlertTriangle, 
    title: "FRAT", 
    desc: "Flight Risk Assessment Tool",
    color: "from-amber-600 to-orange-600"
  },
  { 
    href: "/hems/maintenance", 
    icon: Activity, 
    title: "Maintenance", 
    desc: "Aircraft maintenance tracking",
    color: "from-orange-600 to-red-600"
  },
];

export default function HEMSDashboard() {
  const [data, setData] = useState<HemsDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<HemsDashboardData>("/hems/dashboard", { credentials: "include" })
      .then(setData)
      .catch(() => setError("Failed to load dashboard."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PageShell title="HEMS Operations" requireAuth={true}>
      {/* Header */}
      <div className="relative overflow-hidden bg-gradient-to-r from-sky-950 via-zinc-900 to-blue-950 border-b border-sky-900/30">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
        <div className="relative px-6 py-8">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex items-center gap-4"
          >
            <div className="p-4 bg-gradient-to-br from-sky-500 to-blue-500 rounded-2xl shadow-2xl shadow-sky-500/30">
              <Plane className="w-10 h-10 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-zinc-100 mb-1">HEMS Operations</h1>
              <p className="text-sky-200">Helicopter Emergency Medical Services & Part 135 Compliance</p>
            </div>
          </motion.div>
        </div>
      </div>

      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <div className="inline-flex items-center gap-3 px-6 py-3 bg-zinc-900/50 rounded-full border border-zinc-800">
              <Activity className="w-5 h-5 text-sky-400 animate-pulse" />
              <span className="text-zinc-300">Loading dashboard...</span>
            </div>
          </motion.div>
        )}

        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400"
          >
            {error}
          </motion.div>
        )}

        {data && (
          <>
            {/* Stats Grid */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="grid grid-cols-2 lg:grid-cols-4 gap-4"
            >
              {[
                { label: "Aircraft Available", value: data.aircraft_available, icon: Plane, color: "sky" },
                { label: "Pilots Current", value: data.pilots_current, icon: Users, color: "green" },
                { label: "Flights Today", value: data.flights_today, icon: Activity, color: "blue" },
                { label: "Hours This Month", value: data.flight_hours_month.toFixed(1), icon: Clock, color: "purple" },
              ].map((stat, idx) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2 + idx * 0.1 }}
                  whileHover={{ scale: 1.02, y: -2 }}
                  className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="p-2 bg-zinc-800 rounded-lg">
                      <stat.icon className={`w-5 h-5 text-${stat.color}-400`} />
                    </div>
                  </div>
                  <div className="text-3xl font-bold text-zinc-100 mb-1">{stat.value}</div>
                  <div className="text-sm text-zinc-400">{stat.label}</div>
                </motion.div>
              ))}
            </motion.div>

            {/* Active Missions */}
            {data.active_missions && data.active_missions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-zinc-900/50 backdrop-blur-xl border border-zinc-800 rounded-2xl p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Plane className="w-6 h-6 text-sky-400" />
                    <h2 className="text-xl font-bold text-zinc-100">Active Missions</h2>
                  </div>
                  <Link href="/hems/missions" className="text-sm text-sky-400 hover:text-sky-300">
                    View all
                  </Link>
                </div>
                <div className="space-y-2">
                  {data.active_missions.map((mission, idx) => (
                    <Link key={mission.id} href={`/hems/missions/${mission.id}`}>
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4 + idx * 0.05 }}
                        className="flex items-center justify-between p-4 bg-zinc-800/50 rounded-xl hover:bg-zinc-800 transition-colors cursor-pointer"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-2 h-2 bg-sky-500 rounded-full animate-pulse" />
                          <div>
                            <div className="font-semibold text-zinc-100">{mission.mission_number}</div>
                            <div className="text-sm text-zinc-400">{mission.aircraft}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-zinc-300">{mission.status}</div>
                          <div className="text-xs text-zinc-500">
                            {mission.eta ? `ETA: ${new Date(mission.eta).toLocaleTimeString()}` : 'In Transit'}
                          </div>
                        </div>
                      </motion.div>
                    </Link>
                  ))}
                </div>
              </motion.div>
            )}
          </>
        )}

        {/* HEMS Modules */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <h2 className="text-2xl font-bold text-zinc-100 mb-4">HEMS Modules</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {hemsModules.map((mod, idx) => (
              <motion.div
                key={mod.href}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 + idx * 0.1 }}
                whileHover={{ scale: 1.02, y: -4 }}
              >
                <Link href={mod.href} className="block group">
                  <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-900 to-zinc-800 border border-zinc-700 hover:border-sky-500/50 transition-all duration-300 p-6">
                    <div className={`absolute inset-0 bg-gradient-to-br ${mod.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`} />
                    <div className="relative">
                      <div className={`p-3 bg-gradient-to-br ${mod.color} rounded-xl w-fit mb-4 shadow-lg`}>
                        <mod.icon className="w-8 h-8 text-white" />
                      </div>
                      <h3 className="text-xl font-bold text-zinc-100 group-hover:text-sky-400 transition-colors mb-2">
                        {mod.title}
                      </h3>
                      <p className="text-sm text-zinc-400">{mod.desc}</p>
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Weather & Maintenance Alerts */}
        {data && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-4"
          >
            <div className={`border rounded-2xl p-6 ${
              data.weather_status === 'VFR' 
                ? 'bg-green-500/10 border-green-500/30' 
                : 'bg-amber-500/10 border-amber-500/30'
            }`}>
              <div className="flex items-center gap-3 mb-2">
                <Cloud className={`w-6 h-6 ${data.weather_status === 'VFR' ? 'text-green-400' : 'text-amber-400'}`} />
                <h3 className={`text-lg font-bold ${data.weather_status === 'VFR' ? 'text-green-400' : 'text-amber-400'}`}>
                  Weather Status
                </h3>
              </div>
              <p className="text-zinc-300">Current conditions: {data.weather_status}</p>
            </div>

            {data.maintenance_due > 0 && (
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-2">
                  <AlertTriangle className="w-6 h-6 text-amber-400" />
                  <h3 className="text-lg font-bold text-amber-400">Maintenance Required</h3>
                </div>
                <p className="text-zinc-300">{data.maintenance_due} aircraft require maintenance</p>
              </div>
            )}
          </motion.div>
        )}

        {/* Part 135 Compliance Note */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0 }}
          className="bg-sky-900/20 border border-sky-700 rounded-xl p-4"
        >
          <h3 className="font-bold text-sky-400 mb-2">FAA Part 135 Compliance</h3>
          <p className="text-sm text-zinc-300">
            Aviation compliance tracking includes FAR 135.267 flight/duty time limits, 
            pilot currency requirements, aircraft maintenance intervals, and airworthiness 
            directive tracking. All flight operations must comply with Part 135 regulations.
          </p>
        </motion.div>
      </div>
    </PageShell>
  );
}
