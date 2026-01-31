"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { 
  Flame, MapPin, ClipboardCheck, FileText, Truck, 
  Shield, AlertTriangle, Calendar, Activity, TrendingUp 
} from "lucide-react";
import { PageShell } from "@/components/PageShell";

type FireDashboardData = {
  active_incidents: number;
  apparatus_ready: string;
  training_gap: string;
  risk_indicator: string;
  hydrants_due: number;
  inspections_due: number;
  recent_incidents: Array<{
    id: number;
    incident_number: string;
    incident_type: string;
    address: string;
    timestamp: string;
    status: string;
  }>;
};

const fireModules = [
  { 
    href: "/fire/rms", 
    icon: Flame, 
    title: "Fire RMS", 
    desc: "Records Management System - hydrants, inspections, preplans, CRR", 
    color: "from-red-600 to-orange-600",
    iconColor: "text-red-400"
  },
  { 
    href: "/fire/911-transports", 
    icon: Truck, 
    title: "911 Transports", 
    desc: "Fire-based EMS transport documentation", 
    color: "from-orange-600 to-amber-600",
    iconColor: "text-orange-400"
  },
  { 
    href: "/fire/schedule", 
    icon: Calendar, 
    title: "Scheduling", 
    desc: "Shift scheduling and coverage management", 
    color: "from-amber-600 to-yellow-600",
    iconColor: "text-amber-400"
  },
];

const rmsQuickLinks = [
  { href: "/fire/incidents", label: "Incidents", icon: AlertTriangle, color: "bg-red-500/10 border-red-500/30 hover:border-red-500" },
  { href: "/fire/apparatus", label: "Apparatus", icon: Truck, color: "bg-orange-500/10 border-orange-500/30 hover:border-orange-500" },
  { href: "/fire/hydrants", label: "Hydrants", icon: MapPin, color: "bg-blue-500/10 border-blue-500/30 hover:border-blue-500" },
  { href: "/fire/inspections", label: "Inspections", icon: ClipboardCheck, color: "bg-purple-500/10 border-purple-500/30 hover:border-purple-500" },
  { href: "/fire/preplans", label: "Pre-Plans", icon: FileText, color: "bg-green-500/10 border-green-500/30 hover:border-green-500" },
  { href: "/fire/rms/prevention", label: "CRR Programs", icon: Shield, color: "bg-cyan-500/10 border-cyan-500/30 hover:border-cyan-500" },
  { href: "/fire/rms/ai-risk", label: "AI Risk", icon: TrendingUp, color: "bg-pink-500/10 border-pink-500/30 hover:border-pink-500" },
];

export default function FireDashboard() {
  const [data, setData] = useState<FireDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<FireDashboardData>("/fire/dashboard", { credentials: "include" })
      .then(setData)
      .catch(() => setError("Failed to load dashboard."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PageShell title="Fire Services" requireAuth={true}>
      {/* Header */}
      <div className="relative overflow-hidden bg-gradient-to-r from-red-950 via-zinc-900 to-orange-950 border-b border-red-900/30">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
        <div className="relative px-6 py-8">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex items-center gap-4"
          >
            <div className="p-4 bg-gradient-to-br from-red-500 to-orange-500 rounded-2xl shadow-2xl shadow-red-500/30">
              <Flame className="w-10 h-10 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-zinc-100 mb-1">Fire Services</h1>
              <p className="text-red-200">Comprehensive Fire Department Operations & Records Management</p>
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
              <Activity className="w-5 h-5 text-red-400 animate-pulse" />
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
                { label: "Active Incidents", value: data.active_incidents, color: "red", icon: AlertTriangle, gradient: "from-red-600 to-orange-600" },
                { label: "Apparatus Ready", value: data.apparatus_ready, color: "green", icon: Truck, gradient: "from-green-600 to-emerald-600" },
                { label: "Training Gap", value: data.training_gap, color: "yellow", icon: ClipboardCheck, gradient: "from-yellow-600 to-amber-600" },
                { label: "Risk Indicator", value: data.risk_indicator, color: "orange", icon: TrendingUp, gradient: "from-orange-600 to-red-600" },
              ].map((stat, idx) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2 + idx * 0.1 }}
                  whileHover={{ scale: 1.02, y: -2 }}
                  className="relative group"
                >
                  <div className={`bg-gradient-to-br ${stat.gradient} p-[1px] rounded-2xl`}>
                    <div className="bg-zinc-900 rounded-2xl p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div className="p-2 bg-zinc-800 rounded-lg">
                          <stat.icon className="w-5 h-5 text-red-400" />
                        </div>
                      </div>
                      <div className="text-3xl font-bold text-zinc-100 mb-1">{stat.value}</div>
                      <div className="text-sm text-zinc-400">{stat.label}</div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </motion.div>

            {/* Recent Incidents */}
            {data.recent_incidents && data.recent_incidents.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-zinc-900/50 backdrop-blur-xl border border-zinc-800 rounded-2xl p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="w-6 h-6 text-red-400" />
                    <h2 className="text-xl font-bold text-zinc-100">Recent Incidents</h2>
                  </div>
                  <Link href="/fire/incidents" className="text-sm text-red-400 hover:text-red-300">
                    View all
                  </Link>
                </div>
                <div className="space-y-2">
                  {data.recent_incidents.slice(0, 5).map((incident, idx) => (
                    <Link key={incident.id} href={`/fire/incidents/${incident.id}`}>
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4 + idx * 0.05 }}
                        className="flex items-center justify-between p-4 bg-zinc-800/50 rounded-xl hover:bg-zinc-800 transition-colors cursor-pointer"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                          <div>
                            <div className="font-semibold text-zinc-100">{incident.incident_number}</div>
                            <div className="text-sm text-zinc-400">{incident.incident_type}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-zinc-300">{incident.address}</div>
                          <div className="text-xs text-zinc-500">{new Date(incident.timestamp).toLocaleString()}</div>
                        </div>
                      </motion.div>
                    </Link>
                  ))}
                </div>
              </motion.div>
            )}
          </>
        )}

        {/* Fire Modules */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <h2 className="text-2xl font-bold text-zinc-100 mb-4">Fire Modules</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {fireModules.map((mod, idx) => (
              <motion.div
                key={mod.href}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 + idx * 0.1 }}
                whileHover={{ scale: 1.02, y: -4 }}
              >
                <Link href={mod.href} className="block group">
                  <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-zinc-900 to-zinc-800 border border-zinc-700 hover:border-red-500/50 transition-all duration-300 p-6">
                    <div className={`absolute inset-0 bg-gradient-to-br ${mod.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`} />
                    <div className="relative">
                      <div className={`p-3 bg-gradient-to-br ${mod.color} rounded-xl w-fit mb-4 shadow-lg`}>
                        <mod.icon className="w-8 h-8 text-white" />
                      </div>
                      <h3 className="text-xl font-bold text-zinc-100 group-hover:text-red-400 transition-colors mb-2">
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

        {/* Quick Access */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="bg-zinc-900/50 backdrop-blur-xl border border-zinc-800 rounded-2xl p-6"
        >
          <h2 className="text-xl font-bold text-zinc-100 mb-4">Quick Access - Fire RMS</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {rmsQuickLinks.map((link, idx) => (
              <motion.div
                key={link.href}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.8 + idx * 0.05 }}
                whileHover={{ scale: 1.05, y: -2 }}
              >
                <Link href={link.href}>
                  <div className={`${link.color} border rounded-xl p-4 transition-all duration-200 text-center group`}>
                    <link.icon className="w-6 h-6 mx-auto mb-2 text-zinc-300 group-hover:text-white transition-colors" />
                    <div className="text-sm font-medium text-zinc-300 group-hover:text-white transition-colors">
                      {link.label}
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Due Items Alert */}
        {data && (data.hydrants_due > 0 || data.inspections_due > 0) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="bg-gradient-to-r from-amber-500/10 to-orange-500/10 border border-amber-500/30 rounded-2xl p-6"
          >
            <div className="flex items-start gap-4">
              <AlertTriangle className="w-6 h-6 text-amber-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-bold text-amber-400 mb-2">Attention Required</h3>
                <div className="space-y-1 text-zinc-300">
                  {data.hydrants_due > 0 && (
                    <div>{data.hydrants_due} hydrant{data.hydrants_due > 1 ? 's' : ''} due for inspection</div>
                  )}
                  {data.inspections_due > 0 && (
                    <div>{data.inspections_due} fire inspection{data.inspections_due > 1 ? 's' : ''} due</div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </PageShell>
  );
}
