"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { PageShell } from "@/components/PageShell"

interface Appointment {
  id: string
  providerId: string
  providerName: string
  providerSpecialty: string
  date: string
  time: string
  type: 'in-person' | 'video' | 'phone'
  videoSessionId?: string
}

interface Provider {
  id: string
  name: string
  specialty: string
  rating: number
}

export default function FusionCarePatientDashboard() {
  const router = useRouter()
  const [upcomingAppointments, setUpcomingAppointments] = useState<Appointment[]>([])
  const [featuredProviders, setFeaturedProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      
      // Fetch upcoming appointments
      const appointmentsRes = await fetch('/api/carefusion/patient/appointments?status=upcoming&limit=3', {
        credentials: 'include'
      })
      
      if (appointmentsRes.ok) {
        const appointmentsData = await appointmentsRes.json()
        setUpcomingAppointments(appointmentsData.appointments || [])
      }

      // Fetch featured providers
      const providersRes = await fetch('/api/carefusion/patient/providers?featured=true&limit=3', {
        credentials: 'include'
      })
      
      if (providersRes.ok) {
        const providersData = await providersRes.json()
        setFeaturedProviders(providersData.providers || [])
      }
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err)
    } finally {
      setLoading(false)
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

  return (
    <PageShell title="Patient Portal" requireAuth={true}>
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <p className="text-zinc-400">Welcome to your FusionCare healthcare dashboard</p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <button
            onClick={() => router.push('/portals/carefusion/patient/appointments/book')}
            className="bg-gradient-to-br from-cyan-600 to-cyan-700 hover:from-cyan-700 hover:to-cyan-800 text-white p-6 rounded-xl transition-all"
          >
            <div className="text-3xl mb-2">📅</div>
            <div className="font-semibold">Book Appointment</div>
          </button>
          <button
            onClick={() => router.push('/portals/carefusion/patient/providers')}
            className="bg-gradient-to-br from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white p-6 rounded-xl transition-all"
          >
            <div className="text-3xl mb-2">👨‍⚕️</div>
            <div className="font-semibold">Find Provider</div>
          </button>
          <button
            onClick={() => router.push('/portals/carefusion/patient/medical-records')}
            className="bg-gradient-to-br from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white p-6 rounded-xl transition-all"
          >
            <div className="text-3xl mb-2">📋</div>
            <div className="font-semibold">Medical Records</div>
          </button>
          <button
            onClick={() => router.push('/portals/carefusion/patient/billing')}
            className="bg-gradient-to-br from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white p-6 rounded-xl transition-all"
          >
            <div className="text-3xl mb-2">💳</div>
            <div className="font-semibold">Billing</div>
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Upcoming Appointments */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">Upcoming Appointments</h2>
              <button
                onClick={() => router.push('/portals/carefusion/patient/appointments')}
                className="text-cyan-400 hover:text-cyan-300 text-sm"
              >
                View All →
              </button>
            </div>

            {loading ? (
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
              </div>
            ) : upcomingAppointments.length === 0 ? (
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center">
                <p className="text-zinc-500 mb-4">No upcoming appointments</p>
                <button
                  onClick={() => router.push('/portals/carefusion/patient/appointments/book')}
                  className="text-cyan-400 hover:text-cyan-300"
                >
                  Schedule an appointment
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {upcomingAppointments.map((appointment) => (
                  <div
                    key={appointment.id}
                    className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-cyan-600 transition-all cursor-pointer"
                    onClick={() => router.push(`/portals/carefusion/patient/appointments/${appointment.id}`)}
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex-shrink-0 text-center">
                        <div className="text-2xl font-bold text-cyan-400">
                          {new Date(appointment.date).getDate()}
                        </div>
                        <div className="text-xs text-zinc-400">
                          {new Date(appointment.date).toLocaleDateString('en-US', { month: 'short' })}
                        </div>
                        <div className="text-xs text-zinc-500 mt-1">{appointment.time}</div>
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-lg">{getTypeIcon(appointment.type)}</span>
                          <h3 className="font-semibold truncate">{appointment.providerName}</h3>
                        </div>
                        <p className="text-sm text-zinc-400">{appointment.providerSpecialty}</p>
                      </div>

                      {appointment.type === 'video' && appointment.videoSessionId && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            router.push(`/portals/carefusion/patient/video/${appointment.videoSessionId}`)
                          }}
                          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
                        >
                          Join Video
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Health Insights & Featured Providers */}
          <div className="space-y-6">
            {/* Health Snapshot */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <h2 className="text-xl font-bold mb-4">Health Snapshot</h2>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg">
                  <span className="text-sm text-zinc-400">Recent Visits</span>
                  <button
                    onClick={() => router.push('/portals/carefusion/patient/visits')}
                    className="text-cyan-400 hover:text-cyan-300 font-medium"
                  >
                    View
                  </button>
                </div>
                <div className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg">
                  <span className="text-sm text-zinc-400">Test Results</span>
                  <button
                    onClick={() => router.push('/portals/carefusion/patient/medical-records')}
                    className="text-cyan-400 hover:text-cyan-300 font-medium"
                  >
                    View
                  </button>
                </div>
                <div className="flex items-center justify-between p-3 bg-zinc-800/50 rounded-lg">
                  <span className="text-sm text-zinc-400">Prescriptions</span>
                  <button
                    onClick={() => router.push('/portals/carefusion/patient/medical-records')}
                    className="text-cyan-400 hover:text-cyan-300 font-medium"
                  >
                    View
                  </button>
                </div>
              </div>
            </div>

            {/* Featured Providers */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold">Featured Providers</h2>
                <button
                  onClick={() => router.push('/portals/carefusion/patient/providers')}
                  className="text-cyan-400 hover:text-cyan-300 text-sm"
                >
                  View All →
                </button>
              </div>
              
              {loading ? (
                <div className="flex items-center justify-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-500"></div>
                </div>
              ) : (
                <div className="space-y-3">
                  {featuredProviders.map((provider) => (
                    <div
                      key={provider.id}
                      onClick={() => router.push(`/portals/carefusion/patient/providers/${provider.id}`)}
                      className="flex items-center gap-3 p-3 bg-zinc-800/50 rounded-lg hover:bg-zinc-800 transition-colors cursor-pointer"
                    >
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-sm font-bold flex-shrink-0">
                        {provider.name.split(' ').map(n => n[0]).join('')}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{provider.name}</div>
                        <div className="text-xs text-zinc-400 truncate">{provider.specialty}</div>
                      </div>
                      <div className="flex items-center gap-1 text-yellow-500 text-sm">
                        <span>★</span>
                        <span>{provider.rating.toFixed(1)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Additional Resources */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-2">Virtual Consultations</h3>
            <p className="text-zinc-400 text-sm mb-4">Schedule and join telehealth appointments from anywhere</p>
            <button
              onClick={() => router.push('/portals/carefusion/patient/appointments/book')}
              className="text-cyan-400 hover:text-cyan-300 text-sm font-medium"
            >
              Get Started →
            </button>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-2">Message Your Provider</h3>
            <p className="text-zinc-400 text-sm mb-4">Secure messaging with your healthcare team</p>
            <button
              onClick={() => router.push('/portals/carefusion/patient/messages')}
              className="text-cyan-400 hover:text-cyan-300 text-sm font-medium"
            >
              View Messages →
            </button>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-2">Health Resources</h3>
            <p className="text-zinc-400 text-sm mb-4">Educational materials and wellness tips</p>
            <button
              onClick={() => router.push('/portals/carefusion/patient/resources')}
              className="text-cyan-400 hover:text-cyan-300 text-sm font-medium"
            >
              Explore →
            </button>
          </div>
        </div>
      </div>
    </PageShell>
  )
}
