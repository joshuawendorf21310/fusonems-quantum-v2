"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface Appointment {
  id: string
  providerId: string
  providerName: string
  providerSpecialty: string
  date: string
  time: string
  type: 'in-person' | 'video' | 'phone'
  status: 'upcoming' | 'completed' | 'cancelled'
  reason: string
  videoSessionId?: string
}

export default function AppointmentsPage() {
  const router = useRouter()
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'upcoming' | 'past'>('all')

  useEffect(() => {
    fetchAppointments()
  }, [])

  const fetchAppointments = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/carefusion/patient/appointments', {
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch appointments')
      }
      
      const data = await response.json()
      setAppointments(data.appointments || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleCancelAppointment = async (appointmentId: string) => {
    if (!confirm('Are you sure you want to cancel this appointment?')) {
      return
    }

    try {
      const response = await fetch(`/api/carefusion/patient/appointments/${appointmentId}/cancel`, {
        method: 'POST',
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to cancel appointment')
      }
      
      fetchAppointments()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to cancel appointment')
    }
  }

  const filteredAppointments = appointments.filter(apt => {
    if (filter === 'all') return true
    if (filter === 'upcoming') return apt.status === 'upcoming'
    if (filter === 'past') return apt.status === 'completed' || apt.status === 'cancelled'
    return true
  })

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'video': return '📹'
      case 'phone': return '📞'
      case 'in-person': return '🏥'
      default: return '📅'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'upcoming': return 'text-green-400'
      case 'completed': return 'text-blue-400'
      case 'cancelled': return 'text-red-400'
      default: return 'text-zinc-400'
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-6xl mx-auto p-6 md:p-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/portals/carefusion/patient/dashboard')}
            className="text-cyan-400 hover:text-cyan-300 mb-4 flex items-center gap-2"
          >
            ← Back to Dashboard
          </button>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-cyan-500 to-blue-500 bg-clip-text text-transparent">
                My Appointments
              </h1>
              <p className="text-zinc-400">Manage your healthcare appointments</p>
            </div>
            <button
              onClick={() => router.push('/portals/carefusion/patient/appointments/book')}
              className="px-6 py-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-medium transition-colors"
            >
              Book New Appointment
            </button>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-4 mb-6 border-b border-zinc-800">
          {['all', 'upcoming', 'past'].map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab as any)}
              className={`px-4 py-2 font-medium transition-colors ${
                filter === tab
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-zinc-400 hover:text-zinc-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Appointments List */}
        {!loading && !error && (
          <>
            {filteredAppointments.length === 0 ? (
              <div className="text-center py-12 bg-zinc-900 border border-zinc-800 rounded-xl">
                <p className="text-zinc-500 text-lg mb-4">No appointments found</p>
                <button
                  onClick={() => router.push('/portals/carefusion/patient/appointments/book')}
                  className="text-cyan-400 hover:text-cyan-300"
                >
                  Book your first appointment
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredAppointments.map((appointment) => (
                  <div
                    key={appointment.id}
                    className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-cyan-600 transition-all"
                  >
                    <div className="flex flex-col md:flex-row md:items-center gap-4">
                      {/* Date/Time */}
                      <div className="flex-shrink-0 text-center md:text-left">
                        <div className="text-2xl font-bold text-cyan-400">
                          {new Date(appointment.date).getDate()}
                        </div>
                        <div className="text-sm text-zinc-400">
                          {new Date(appointment.date).toLocaleDateString('en-US', { month: 'short' })}
                        </div>
                        <div className="text-sm text-zinc-500 mt-1">
                          {appointment.time}
                        </div>
                      </div>

                      {/* Details */}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xl">{getTypeIcon(appointment.type)}</span>
                          <h3 className="text-xl font-semibold">{appointment.providerName}</h3>
                        </div>
                        <p className="text-zinc-400 mb-1">{appointment.providerSpecialty}</p>
                        <p className="text-zinc-500 text-sm mb-2">{appointment.reason}</p>
                        <div className="flex gap-3 text-sm">
                          <span className={`font-medium ${getStatusColor(appointment.status)}`}>
                            {appointment.status.charAt(0).toUpperCase() + appointment.status.slice(1)}
                          </span>
                          <span className="text-zinc-500">•</span>
                          <span className="text-zinc-400 capitalize">{appointment.type}</span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex flex-col gap-2 flex-shrink-0">
                        <button
                          onClick={() => router.push(`/portals/carefusion/patient/appointments/${appointment.id}`)}
                          className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition-colors"
                        >
                          View Details
                        </button>
                        {appointment.status === 'upcoming' && appointment.type === 'video' && appointment.videoSessionId && (
                          <button
                            onClick={() => router.push(`/portals/carefusion/patient/video/${appointment.videoSessionId}`)}
                            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
                          >
                            Join Video Call
                          </button>
                        )}
                        {appointment.status === 'upcoming' && (
                          <button
                            onClick={() => handleCancelAppointment(appointment.id)}
                            className="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg text-sm font-medium transition-colors"
                          >
                            Cancel
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
