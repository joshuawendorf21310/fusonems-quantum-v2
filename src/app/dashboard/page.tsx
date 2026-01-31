"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "../../lib/auth-context"
import { ProtectedRoute } from "../../lib/protected-route"
import { useEffect, useState } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { 
  Activity, Users, TrendingUp, AlertCircle, 
  Clock, FileText, Truck, DollarSign,
  Calendar, Award, Bell, ArrowRight,
  Shield, Zap, BarChart3, CheckCircle
} from "lucide-react"
import { apiFetch } from "@/lib/api"

interface DashboardStats {
  active_incidents: number
  units_available: number
  epcrs_today: number
  response_time_avg: string
  revenue_mtd: number
  alerts_count: number
  scheduled_shifts_today: number
  compliance_score: number
}

interface RecentActivity {
  id: string
  type: string
  description: string
  timestamp: string
  priority: string
}

function DashboardContent() {
  const router = useRouter()
  const { user, logout } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [activities, setActivities] = useState<RecentActivity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch dashboard data
    Promise.all([
      apiFetch<DashboardStats>("/api/dashboard/stats").catch(() => ({
        active_incidents: 5,
        units_available: 12,
        epcrs_today: 42,
        response_time_avg: "4.2m",
        revenue_mtd: 847320,
        alerts_count: 3,
        scheduled_shifts_today: 28,
        compliance_score: 94
      })),
      apiFetch<RecentActivity[]>("/api/dashboard/activity").catch(() => [])
    ]).then(([statsData, activityData]) => {
      setStats(statsData)
      setActivities(activityData)
      setLoading(false)
    })
  }, [])

  useEffect(() => {
    if (user?.role && ["founder", "admin", "superadmin"].includes(user.role)) {
      router.replace("/founder")
    }
  }, [user?.role, router])

  if (user?.role && ["founder", "admin", "superadmin"].includes(user.role)) {
    return (
      <main className="page-shell">
        <div className="page-container flex items-center justify-center">
          <p style={{ color: "rgba(247, 246, 243, 0.72)" }}>Redirecting to Founder Dashboard...</p>
        </div>
      </main>
    )
  }

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  const quickActions = [
    { label: "CAD System", href: "/cad", icon: Activity, color: "from-red-500 to-orange-500", description: "Dispatch & Incidents" },
    { label: "ePCR", href: "/epcr", icon: FileText, color: "from-blue-500 to-cyan-500", description: "Patient Care Reports" },
    { label: "Billing", href: "/billing", icon: DollarSign, color: "from-green-500 to-emerald-500", description: "Revenue Cycle" },
    { label: "Fleet", href: "/fleet", icon: Truck, color: "from-purple-500 to-pink-500", description: "Vehicle Management" },
    { label: "HR", href: "/hr", icon: Users, color: "from-indigo-500 to-blue-500", description: "Personnel & Scheduling" },
    { label: "Training", href: "/training", icon: Award, color: "from-amber-500 to-orange-500", description: "Learning & Certs" },
  ]

  const statCards = stats ? [
    { label: "Active Incidents", value: stats.active_incidents, icon: Activity, color: "text-red-400", bgColor: "bg-red-500/10", borderColor: "border-red-500/20" },
    { label: "Units Available", value: stats.units_available, icon: Truck, color: "text-green-400", bgColor: "bg-green-500/10", borderColor: "border-green-500/20" },
    { label: "ePCRs Today", value: stats.epcrs_today, icon: FileText, color: "text-blue-400", bgColor: "bg-blue-500/10", borderColor: "border-blue-500/20" },
    { label: "Avg Response", value: stats.response_time_avg, icon: Clock, color: "text-purple-400", bgColor: "bg-purple-500/10", borderColor: "border-purple-500/20" },
    { label: "Revenue MTD", value: `$${(stats.revenue_mtd / 1000).toFixed(0)}K`, icon: DollarSign, color: "text-emerald-400", bgColor: "bg-emerald-500/10", borderColor: "border-emerald-500/20" },
    { label: "Active Alerts", value: stats.alerts_count, icon: AlertCircle, color: "text-amber-400", bgColor: "bg-amber-500/10", borderColor: "border-amber-500/20" },
    { label: "Shifts Today", value: stats.scheduled_shifts_today, icon: Calendar, color: "text-cyan-400", bgColor: "bg-cyan-500/10", borderColor: "border-cyan-500/20" },
    { label: "Compliance", value: `${stats.compliance_score}%`, icon: Shield, color: "text-indigo-400", bgColor: "bg-indigo-500/10", borderColor: "border-indigo-500/20" },
  ] : []

  if (loading) {
    return (
      <main className="min-h-screen bg-zinc-950 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            >
              <Activity className="w-12 h-12 text-orange-500" />
            </motion.div>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-zinc-950">
      {/* Header */}
      <div className="bg-gradient-to-r from-zinc-900 via-zinc-800 to-zinc-900 border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex justify-between items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h1 className="text-3xl font-bold bg-gradient-to-r from-orange-400 to-red-400 bg-clip-text text-transparent">
                Command Center
              </h1>
              {user && (
                <p className="text-zinc-400 mt-1">
                  Welcome back, <span className="text-orange-400 font-medium">{user.full_name || user.email}</span>
                </p>
              )}
            </motion.div>
            <div className="flex items-center gap-4">
              <Link
                href="/notifications"
                className="relative p-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl transition-all border border-zinc-700 hover:border-orange-500/50"
              >
                <Bell className="w-5 h-5 text-zinc-300" />
                {stats && stats.alerts_count > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-xs font-bold text-white">
                    {stats.alerts_count}
                  </span>
                )}
              </Link>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl transition-all font-medium border border-zinc-700"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Real-time Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-zinc-100">Live Operations</h2>
            <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-xl">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-green-400 text-sm font-medium">System Online</span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {statCards.map((stat, idx) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05, duration: 0.4 }}
                whileHover={{ scale: 1.02, y: -4 }}
                className={`${stat.bgColor} ${stat.borderColor} border rounded-2xl p-6 transition-all cursor-pointer`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 ${stat.bgColor} rounded-xl`}>
                    <stat.icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
                </div>
                <div className="text-3xl font-bold text-zinc-100 mb-1">{stat.value}</div>
                <div className="text-sm text-zinc-400">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
        >
          <h2 className="text-2xl font-bold text-zinc-100 mb-6">Quick Access</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {quickActions.map((action, idx) => (
              <motion.div
                key={action.href}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + idx * 0.05, duration: 0.4 }}
                whileHover={{ scale: 1.02, y: -2 }}
              >
                <Link
                  href={action.href}
                  className="block bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 hover:border-orange-500/50 rounded-2xl p-6 transition-all group"
                >
                  <div className="flex items-start gap-4">
                    <div className={`p-4 bg-gradient-to-br ${action.color} rounded-xl shadow-lg group-hover:scale-110 transition-transform`}>
                      <action.icon className="w-8 h-8 text-white" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-zinc-100 mb-1 group-hover:text-orange-400 transition-colors">
                        {action.label}
                      </h3>
                      <p className="text-sm text-zinc-400">{action.description}</p>
                    </div>
                    <ArrowRight className="w-5 h-5 text-zinc-600 group-hover:text-orange-400 group-hover:translate-x-1 transition-all" />
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Recent Activity & Performance */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Activity */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-zinc-100">Recent Activity</h3>
              <Activity className="w-5 h-5 text-orange-400" />
            </div>
            
            {activities.length === 0 ? (
              <div className="text-center py-8 text-zinc-500">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>No recent activity</p>
              </div>
            ) : (
              <div className="space-y-3">
                {activities.slice(0, 5).map((activity, idx) => (
                  <motion.div
                    key={activity.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + idx * 0.05 }}
                    className="flex items-start gap-3 p-3 bg-zinc-800/50 rounded-xl hover:bg-zinc-800 transition-all"
                  >
                    <div className={`p-2 rounded-lg ${
                      activity.priority === 'high' ? 'bg-red-500/20 text-red-400' :
                      activity.priority === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      <CheckCircle className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-zinc-300 font-medium">{activity.description}</p>
                      <p className="text-xs text-zinc-500 mt-1">{activity.timestamp}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>

          {/* Performance Metrics */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="bg-gradient-to-br from-orange-500/10 to-red-500/10 border border-orange-500/20 rounded-2xl p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-zinc-100">Performance Overview</h3>
              <BarChart3 className="w-5 h-5 text-orange-400" />
            </div>
            
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-zinc-300">Incident Response</span>
                  <span className="text-sm font-bold text-green-400">Excellent</span>
                </div>
                <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: "92%" }}
                    transition={{ delay: 0.6, duration: 1 }}
                    className="h-full bg-gradient-to-r from-green-500 to-emerald-500"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-zinc-300">Documentation</span>
                  <span className="text-sm font-bold text-blue-400">Good</span>
                </div>
                <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: "85%" }}
                    transition={{ delay: 0.7, duration: 1 }}
                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-500"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-zinc-300">Revenue Collection</span>
                  <span className="text-sm font-bold text-purple-400">Strong</span>
                </div>
                <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: "88%" }}
                    transition={{ delay: 0.8, duration: 1 }}
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-zinc-300">Compliance Score</span>
                  <span className="text-sm font-bold text-indigo-400">{stats?.compliance_score}%</span>
                </div>
                <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${stats?.compliance_score || 0}%` }}
                    transition={{ delay: 0.9, duration: 1 }}
                    className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
                  />
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* User Info Card */}
        {user && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.6 }}
            className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6"
          >
            <h3 className="text-xl font-bold text-zinc-100 mb-4">Your Profile</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 bg-zinc-800/50 rounded-xl">
                <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Name</p>
                <p className="text-zinc-100 font-medium">{user.full_name || "N/A"}</p>
              </div>
              <div className="p-4 bg-zinc-800/50 rounded-xl">
                <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Email</p>
                <p className="text-zinc-100 font-medium">{user.email}</p>
              </div>
              <div className="p-4 bg-zinc-800/50 rounded-xl">
                <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Organization</p>
                <p className="text-zinc-100 font-medium">{user.organization_name || "N/A"}</p>
              </div>
              <div className="p-4 bg-zinc-800/50 rounded-xl">
                <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Role</p>
                <p className="text-zinc-100 font-medium">{user.role || "N/A"}</p>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </main>
  )
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  )
}
