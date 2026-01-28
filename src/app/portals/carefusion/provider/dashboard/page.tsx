"use client"

import { useState, useEffect } from "react"
import Link from "next/link"

interface TodayAppointment {
  id: string
  patientId: string
  patientName: string
  patientMrn: string
  time: string
  type: string
  status: string
  reason: string
}

interface PatientInQueue {
  id: string
  patientId: string
  patientName: string
  waitTime: string
  priority: string
  reason: string
}

interface DashboardStats {
  todayAppointments: number
  patientsInQueue: number
  completedVisits: number
  pendingPrescriptions: number
}

export default function CareFusionProviderDashboard() {
  const [appointments, setAppointments] = useState<TodayAppointment[]>([])
  const [queue, setQueue] = useState<PatientInQueue[]>([])
  const [stats, setStats] = useState<DashboardStats>({
    todayAppointments: 0,
    patientsInQueue: 0,
    completedVisits: 0,
    pendingPrescriptions: 0
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const response = await fetch("/api/carefusion/provider/dashboard", {
        credentials: "include"
      })
      
      if (!response.ok) throw new Error("Failed to fetch dashboard data")
      
      const data = await response.json()
      setAppointments(data.todayAppointments || [])
      setQueue(data.patientQueue || [])
      setStats(data.stats || stats)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error loading dashboard")
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "scheduled":
        return "bg-blue-950/50 text-blue-400 border-blue-800"
      case "confirmed":
        return "bg-green-950/50 text-green-400 border-green-800"
      case "in-progress":
        return "bg-purple-950/50 text-purple-400 border-purple-800"
      case "completed":
        return "bg-zinc-800 text-zinc-400 border-zinc-700"
      default:
        return "bg-zinc-800 text-zinc-400 border-zinc-700"
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "urgent":
        return "bg-red-950/50 text-red-400 border-red-800"
      case "high":
        return "bg-orange-950/50 text-orange-400 border-orange-800"
      default:
        return "bg-zinc-800 text-zinc-400 border-zinc-700"
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-400">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
            Provider Dashboard
          </h1>
          <p className="text-zinc-400">Welcome back, Dr. Provider</p>
        </div>

        {error && (
          <div className="bg-red-950/50 border border-red-800 text-red-300 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400 mb-1">Today's Appointments</p>
                <p className="text-3xl font-bold">{stats.todayAppointments}</p>
              </div>
              <div className="w-12 h-12 bg-blue-950/50 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400 mb-1">Patients in Queue</p>
                <p className="text-3xl font-bold">{stats.patientsInQueue}</p>
              </div>
              <div className="w-12 h-12 bg-purple-950/50 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400 mb-1">Completed Visits</p>
                <p className="text-3xl font-bold">{stats.completedVisits}</p>
              </div>
              <div className="w-12 h-12 bg-green-950/50 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400 mb-1">Pending Prescriptions</p>
                <p className="text-3xl font-bold">{stats.pendingPrescriptions}</p>
              </div>
              <div className="w-12 h-12 bg-orange-950/50 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Today's Appointments</h2>
              <Link
                href="/portals/carefusion/provider/appointments"
                className="text-purple-400 hover:text-purple-300 text-sm font-medium"
              >
                View All
              </Link>
            </div>
            <div className="divide-y divide-zinc-800 max-h-96 overflow-y-auto">
              {appointments.length === 0 ? (
                <div className="px-6 py-8 text-center text-zinc-500">
                  No appointments scheduled for today
                </div>
              ) : (
                appointments.map((apt) => (
                  <div key={apt.id} className="px-6 py-4 hover:bg-zinc-800/50 transition">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="text-lg font-bold text-purple-400">{apt.time}</div>
                        <div>
                          <div className="font-medium">{apt.patientName}</div>
                          <div className="text-xs text-zinc-500">MRN: {apt.patientMrn}</div>
                        </div>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(apt.status)}`}>
                        {apt.status}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-zinc-400">{apt.reason}</span>
                      <Link
                        href={`/portals/carefusion/provider/patients/${apt.patientId}`}
                        className="text-purple-400 hover:text-purple-300 font-medium"
                      >
                        View Chart
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-zinc-800">
              <h2 className="text-xl font-semibold">Patient Queue</h2>
            </div>
            <div className="divide-y divide-zinc-800 max-h-96 overflow-y-auto">
              {queue.length === 0 ? (
                <div className="px-6 py-8 text-center text-zinc-500">
                  No patients in queue
                </div>
              ) : (
                queue.map((patient) => (
                  <div key={patient.id} className="px-6 py-4 hover:bg-zinc-800/50 transition">
                    <div className="flex items-center justify-between mb-2">
                      <div className="font-medium">{patient.patientName}</div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(patient.priority)}`}>
                        {patient.priority}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-zinc-400">{patient.reason}</span>
                      <span className="text-xs text-zinc-500">Wait: {patient.waitTime}</span>
                    </div>
                    <div className="mt-2">
                      <Link
                        href={`/portals/carefusion/provider/visits/new?patientId=${patient.patientId}`}
                        className="text-purple-400 hover:text-purple-300 text-sm font-medium"
                      >
                        Start Visit
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Link
            href="/portals/carefusion/provider/patients"
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:bg-zinc-800/50 transition"
          >
            <div className="flex items-center gap-4 mb-3">
              <div className="w-12 h-12 bg-purple-950/50 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold">Patient List</h3>
            </div>
            <p className="text-sm text-zinc-400">View and manage patient records</p>
          </Link>

          <Link
            href="/portals/carefusion/provider/schedule"
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:bg-zinc-800/50 transition"
          >
            <div className="flex items-center gap-4 mb-3">
              <div className="w-12 h-12 bg-blue-950/50 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold">Schedule</h3>
            </div>
            <p className="text-sm text-zinc-400">Manage availability and time slots</p>
          </Link>

          <Link
            href="/portals/carefusion/provider/visits"
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:bg-zinc-800/50 transition"
          >
            <div className="flex items-center gap-4 mb-3">
              <div className="w-12 h-12 bg-green-950/50 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold">Visits</h3>
            </div>
            <p className="text-sm text-zinc-400">Document patient encounters</p>
          </Link>

          <Link
            href="/portals/carefusion/provider/prescriptions"
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:bg-zinc-800/50 transition"
          >
            <div className="flex items-center gap-4 mb-3">
              <div className="w-12 h-12 bg-orange-950/50 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold">Prescriptions</h3>
            </div>
            <p className="text-sm text-zinc-400">E-prescribing interface</p>
          </Link>
        </div>
      </div>
    </div>
  )
}
