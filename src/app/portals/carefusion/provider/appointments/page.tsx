"use client"

import { useState, useEffect } from "react"
import Link from "next/link"

interface Appointment {
  id: string
  patientId: string
  patientName: string
  patientMrn: string
  appointmentDate: string
  appointmentTime: string
  duration: number
  type: string
  status: string
  reason: string
  notes?: string
}

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterStatus, setFilterStatus] = useState("all")
  const [filterDate, setFilterDate] = useState("")

  useEffect(() => {
    fetchAppointments()
  }, [])

  const fetchAppointments = async () => {
    try {
      setLoading(true)
      const response = await fetch("/api/carefusion/provider/appointments", {
        credentials: "include"
      })
      
      if (!response.ok) throw new Error("Failed to fetch appointments")
      
      const data = await response.json()
      setAppointments(data.appointments || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error loading appointments")
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateStatus = async (appointmentId: string, newStatus: string) => {
    try {
      const response = await fetch(`/api/carefusion/provider/appointments/${appointmentId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ status: newStatus })
      })

      if (!response.ok) throw new Error("Failed to update appointment status")

      await fetchAppointments()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error updating status")
    }
  }

  const filteredAppointments = appointments.filter(apt => {
    const matchesStatus = filterStatus === "all" || apt.status === filterStatus
    const matchesDate = !filterDate || apt.appointmentDate === filterDate
    return matchesStatus && matchesDate
  })

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
      case "cancelled":
        return "bg-red-950/50 text-red-400 border-red-800"
      case "no-show":
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
          <p className="text-zinc-400">Loading appointments...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
            Appointments
          </h1>
          <p className="text-zinc-400">Manage patient appointments and status</p>
        </div>

        {error && (
          <div className="bg-red-950/50 border border-red-800 text-red-300 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div>
              <input
                type="date"
                value={filterDate}
                onChange={(e) => setFilterDate(e.target.value)}
                className="px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="all">All Status</option>
              <option value="scheduled">Scheduled</option>
              <option value="confirmed">Confirmed</option>
              <option value="in-progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="no-show">No Show</option>
            </select>
            <button
              onClick={() => {
                setFilterDate("")
                setFilterStatus("all")
              }}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg transition"
            >
              Clear Filters
            </button>
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-zinc-950 border-b border-zinc-800">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Date & Time</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Patient</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Type</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Reason</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Duration</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Status</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {filteredAppointments.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-zinc-500">
                    No appointments found
                  </td>
                </tr>
              ) : (
                filteredAppointments.map((apt) => (
                  <tr key={apt.id} className="hover:bg-zinc-800/50 transition">
                    <td className="px-6 py-4">
                      <div className="font-medium">{apt.appointmentDate}</div>
                      <div className="text-sm text-zinc-400">{apt.appointmentTime}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium">{apt.patientName}</div>
                      <div className="text-xs text-zinc-500 font-mono">MRN: {apt.patientMrn}</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-zinc-400 capitalize">{apt.type}</td>
                    <td className="px-6 py-4 text-sm text-zinc-400">{apt.reason}</td>
                    <td className="px-6 py-4 text-sm text-zinc-400">{apt.duration} min</td>
                    <td className="px-6 py-4">
                      <select
                        value={apt.status}
                        onChange={(e) => handleUpdateStatus(apt.id, e.target.value)}
                        className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(apt.status)} bg-transparent`}
                      >
                        <option value="scheduled">Scheduled</option>
                        <option value="confirmed">Confirmed</option>
                        <option value="in-progress">In Progress</option>
                        <option value="completed">Completed</option>
                        <option value="cancelled">Cancelled</option>
                        <option value="no-show">No Show</option>
                      </select>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <Link
                          href={`/portals/carefusion/provider/patients/${apt.patientId}`}
                          className="text-purple-400 hover:text-purple-300 text-sm font-medium"
                        >
                          View Patient
                        </Link>
                        {apt.status === "confirmed" && (
                          <Link
                            href={`/portals/carefusion/provider/visits/new?appointmentId=${apt.id}`}
                            className="text-green-400 hover:text-green-300 text-sm font-medium"
                          >
                            Start Visit
                          </Link>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
