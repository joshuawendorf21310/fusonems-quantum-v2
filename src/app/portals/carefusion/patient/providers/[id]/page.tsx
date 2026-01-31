"use client"

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'

interface Provider {
  id: string
  name: string
  specialty: string
  credentials: string
  photoUrl?: string
  rating: number
  yearsExperience: number
  acceptingNewPatients: boolean
  bio: string
  education: string[]
  certifications: string[]
  languages: string[]
  hospitalAffiliations: string[]
  availability: {
    day: string
    slots: string[]
  }[]
}

export default function ProviderDetailPage() {
  const router = useRouter()
  const params = useParams()
  const providerId = params.id as string

  const [provider, setProvider] = useState<Provider | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (providerId) {
      fetchProvider()
    }
  }, [providerId])

  const fetchProvider = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/carefusion/patient/providers/${providerId}`, {
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch provider details')
      }
      
      const data = await response.json()
      setProvider(data.provider)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleBookAppointment = () => {
    router.push(`/portals/carefusion/patient/appointments/book?providerId=${providerId}`)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    )
  }

  if (error || !provider) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-6">
            <p className="text-red-400">{error || 'Provider not found'}</p>
          </div>
          <button
            onClick={() => router.push('/portals/carefusion/patient/providers')}
            className="mt-4 text-cyan-400 hover:text-cyan-300"
          >
            ← Back to Providers
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-5xl mx-auto p-6 md:p-8">
        {/* Back Button */}
        <button
          onClick={() => router.push('/portals/carefusion/patient/providers')}
          className="text-cyan-400 hover:text-cyan-300 mb-6 flex items-center gap-2"
        >
          ← Back to Providers
        </button>

        {/* Provider Header */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 mb-6">
          <div className="flex flex-col md:flex-row gap-6">
            {/* Photo */}
            <div className="w-32 h-32 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-4xl font-bold flex-shrink-0">
              {provider.photoUrl ? (
                <img
                  src={provider.photoUrl}
                  alt={provider.name}
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                provider.name.split(' ').map(n => n[0]).join('')
              )}
            </div>

            {/* Info */}
            <div className="flex-1">
              <h1 className="text-3xl font-bold mb-2">{provider.name}</h1>
              <p className="text-zinc-400 text-lg mb-4">{provider.credentials}</p>
              
              <div className="flex flex-wrap gap-3 mb-4">
                <span className="px-4 py-2 bg-cyan-600/20 text-cyan-400 rounded-full text-sm font-medium">
                  {provider.specialty}
                </span>
                <span className="px-4 py-2 bg-zinc-800 text-zinc-300 rounded-full text-sm flex items-center gap-2">
                  <span className="text-yellow-500">★</span>
                  {provider.rating.toFixed(1)}
                </span>
                <span className="px-4 py-2 bg-zinc-800 text-zinc-300 rounded-full text-sm">
                  {provider.yearsExperience} years exp.
                </span>
              </div>

              <div className="mb-6">
                {provider.acceptingNewPatients ? (
                  <span className="text-green-400 flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                    Accepting new patients
                  </span>
                ) : (
                  <span className="text-red-400 flex items-center gap-2">
                    <span className="w-2 h-2 bg-red-400 rounded-full"></span>
                    Not accepting new patients
                  </span>
                )}
              </div>

              {provider.acceptingNewPatients && (
                <button
                  onClick={handleBookAppointment}
                  className="px-6 py-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-medium transition-colors"
                >
                  Book Appointment
                </button>
              )}
            </div>
          </div>
        </div>

        {/* About */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-6">
          <h2 className="text-2xl font-bold mb-4">About</h2>
          <p className="text-zinc-300 leading-relaxed">{provider.bio}</p>
        </div>

        {/* Education & Credentials */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-bold mb-4">Education</h2>
            <ul className="space-y-2">
              {provider.education.map((edu, index) => (
                <li key={index} className="text-zinc-300 flex items-start gap-2">
                  <span className="text-cyan-400">•</span>
                  {edu}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-bold mb-4">Certifications</h2>
            <ul className="space-y-2">
              {provider.certifications.map((cert, index) => (
                <li key={index} className="text-zinc-300 flex items-start gap-2">
                  <span className="text-cyan-400">•</span>
                  {cert}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Languages & Affiliations */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-bold mb-4">Languages</h2>
            <div className="flex flex-wrap gap-2">
              {provider.languages.map((lang, index) => (
                <span key={index} className="px-3 py-1 bg-zinc-800 text-zinc-300 rounded-full text-sm">
                  {lang}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-bold mb-4">Hospital Affiliations</h2>
            <ul className="space-y-2">
              {provider.hospitalAffiliations.map((hospital, index) => (
                <li key={index} className="text-zinc-300 flex items-start gap-2">
                  <span className="text-cyan-400">•</span>
                  {hospital}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Availability */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-2xl font-bold mb-4">Typical Availability</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {provider.availability.map((schedule, index) => (
              <div key={index} className="bg-zinc-800/50 rounded-lg p-4">
                <h3 className="font-semibold text-cyan-400 mb-2">{schedule.day}</h3>
                <div className="space-y-1">
                  {schedule.slots.map((slot, slotIndex) => (
                    <div key={slotIndex} className="text-sm text-zinc-300">
                      {slot}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
