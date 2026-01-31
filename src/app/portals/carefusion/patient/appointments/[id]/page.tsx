"use client"

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'

interface Appointment {
  id: string
  providerId: string
  providerName: string
  providerSpecialty: string
  providerPhotoUrl?: string
  date: string
  time: string
  type: 'in-person' | 'video' | 'phone'
  status: 'upcoming' | 'completed' | 'cancelled'
  reason: string
  notes?: string
  videoSessionId?: string
  location?: string
  phoneNumber?: string
}

export default function AppointmentDetailPage() {
  const router = useRouter()
  const params = useParams()
  const appointmentId = params.id as string

  const [appointment, setAppointment] = useState<Appointment | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (appointmentId) {
      fetchAppointment()
    }
  }, [appointmentId])

  const fetchAppointment = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/carefusion/patient/appointments/${appointmentId}`, {
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch appointment details')
      }
      
      const data = await response.json()
      setAppointment(data.appointment)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleCancelAppointment = async () => {
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
      
      router.push('/portals/carefusion/patient/appointments')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to cancel appointment')
    }
  }

  const handleReschedule = () => {
    router.push(`/portals/carefusion/patient/appointments/book?providerId=${appointment?.providerId}`)
  }

  const handleJoinVideo = () => {
    if (appointment?.videoSessionId) {
      router.push(`/portals/carefusion/patient/video/${appointment.videoSessionId}`)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'upcoming': return 'bg-green-600/20 text-green-400 border-green-800'
      case 'completed': return 'bg-blue-600/20 text-blue-400 border-blue-800'
      case 'cancelled': return 'bg-red-600/20 text-red-400 border-red-800'
      default: return 'bg-zinc-800 text-zinc-400 border-zinc-700'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'video': return '📹'
      case 'phone': return '📞'
      case 'in-person': return '🏥'
      default: return '📅'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    )
  }

  if (error || !appointment) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-6">
            <p className="text-red-400">{error || 'Appointment not found'}</p>
          </div>
          <button
            onClick={() => router.push('/portals/carefusion/patient/appointments')}
            className="mt-4 text-cyan-400 hover:text-cyan-300"
          >
            ← Back to Appointments
          </button>
        </div>
      </div>
    )
  }

  const appointmentDateTime = new Date(`${appointment.date}T${appointment.time}`)
  const isUpcoming = appointment.status === 'upcoming'
  const canJoinVideo = isUpcoming && appointment.type === 'video' && appointment.videoSessionId

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-4xl mx-auto p-6 md:p-8">
        {/* Back Button */}
        <button
          onClick={() => router.push('/portals/carefusion/patient/appointments')}
          className="text-cyan-400 hover:text-cyan-300 mb-6 flex items-center gap-2"
        >
          ← Back to Appointments
        </button>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-500 to-blue-500 bg-clip-text text-transparent">
              Appointment Details
            </h1>
            <span className={`px-4 py-1 rounded-full text-sm font-medium border ${getStatusColor(appointment.status)}`}>
              {appointment.status.charAt(0).toUpperCase() + appointment.status.slice(1)}
            </span>
          </div>
        </div>

        {/* Video Call Button (if applicable) */}
        {canJoinVideo && (
          <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-xl p-6 mb-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Video Consultation Ready</h2>
                <p className="text-green-100">Join your video appointment with {appointment.providerName}</p>
              </div>
              <button
                onClick={handleJoinVideo}
                className="px-8 py-4 bg-white text-green-600 rounded-lg font-bold text-lg hover:bg-green-50 transition-colors"
              >
                Join Video Call
              </button>
            </div>
          </div>
        )}

        {/* Provider Info */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">Provider Information</h2>
          <div className="flex items-center gap-4">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-2xl font-bold flex-shrink-0">
              {appointment.providerPhotoUrl ? (
                <img
                  src={appointment.providerPhotoUrl}
                  alt={appointment.providerName}
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                appointment.providerName.split(' ').map(n => n[0]).join('')
              )}
            </div>
            <div>
              <h3 className="text-2xl font-semibold">{appointment.providerName}</h3>
              <p className="text-zinc-400">{appointment.providerSpecialty}</p>
              <button
                onClick={() => router.push(`/portals/carefusion/patient/providers/${appointment.providerId}`)}
                className="text-cyan-400 hover:text-cyan-300 text-sm mt-1"
              >
                View Profile →
              </button>
            </div>
          </div>
        </div>

        {/* Appointment Details */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">Appointment Details</h2>
          <div className="space-y-4">
            <div className="flex items-start gap-4 py-3 border-b border-zinc-800">
              <span className="text-2xl">{getTypeIcon(appointment.type)}</span>
              <div className="flex-1">
                <div className="text-zinc-400 text-sm mb-1">Type</div>
                <div className="font-medium capitalize">{appointment.type} Consultation</div>
              </div>
            </div>

            <div className="flex items-start gap-4 py-3 border-b border-zinc-800">
              <span className="text-2xl">📅</span>
              <div className="flex-1">
                <div className="text-zinc-400 text-sm mb-1">Date</div>
                <div className="font-medium">
                  {appointmentDateTime.toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </div>
              </div>
            </div>

            <div className="flex items-start gap-4 py-3 border-b border-zinc-800">
              <span className="text-2xl">🕐</span>
              <div className="flex-1">
                <div className="text-zinc-400 text-sm mb-1">Time</div>
                <div className="font-medium">{appointment.time}</div>
              </div>
            </div>

            {appointment.type === 'in-person' && appointment.location && (
              <div className="flex items-start gap-4 py-3 border-b border-zinc-800">
                <span className="text-2xl">📍</span>
                <div className="flex-1">
                  <div className="text-zinc-400 text-sm mb-1">Location</div>
                  <div className="font-medium">{appointment.location}</div>
                </div>
              </div>
            )}

            {appointment.type === 'phone' && appointment.phoneNumber && (
              <div className="flex items-start gap-4 py-3 border-b border-zinc-800">
                <span className="text-2xl">📞</span>
                <div className="flex-1">
                  <div className="text-zinc-400 text-sm mb-1">Phone Number</div>
                  <div className="font-medium">{appointment.phoneNumber}</div>
                </div>
              </div>
            )}

            <div className="flex items-start gap-4 py-3">
              <span className="text-2xl">📋</span>
              <div className="flex-1">
                <div className="text-zinc-400 text-sm mb-1">Reason for Visit</div>
                <div className="text-zinc-300">{appointment.reason}</div>
              </div>
            </div>

            {appointment.notes && (
              <div className="flex items-start gap-4 py-3 border-t border-zinc-800">
                <span className="text-2xl">📝</span>
                <div className="flex-1">
                  <div className="text-zinc-400 text-sm mb-1">Additional Notes</div>
                  <div className="text-zinc-300">{appointment.notes}</div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        {isUpcoming && (
          <div className="flex flex-col md:flex-row gap-3">
            <button
              onClick={handleReschedule}
              className="flex-1 py-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-medium transition-colors"
            >
              Reschedule Appointment
            </button>
            <button
              onClick={handleCancelAppointment}
              className="flex-1 py-3 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-800 rounded-lg font-medium transition-colors"
            >
              Cancel Appointment
            </button>
          </div>
        )}

        {/* Instructions */}
        {isUpcoming && (
          <div className="mt-6 bg-blue-900/20 border border-blue-800 rounded-lg p-4">
            <h3 className="font-semibold text-blue-400 mb-2">Preparation Tips</h3>
            <ul className="text-sm text-blue-300 space-y-1">
              <li>• Have your insurance information ready</li>
              <li>• Prepare a list of current medications</li>
              <li>• Write down any questions or concerns</li>
              {appointment.type === 'video' && <li>• Test your camera and microphone before the call</li>}
              {appointment.type === 'in-person' && <li>• Arrive 15 minutes early for check-in</li>}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
