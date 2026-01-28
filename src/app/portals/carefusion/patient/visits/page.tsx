"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface Visit {
  id: string
  providerId: string
  providerName: string
  providerSpecialty: string
  date: string
  type: 'in-person' | 'video' | 'phone'
  diagnosis: string
  prescriptions: string[]
  notes: string
  followUpRequired: boolean
  documentIds?: string[]
}

export default function VisitsPage() {
  const router = useRouter()
  const [visits, setVisits] = useState<Visit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedVisit, setExpandedVisit] = useState<string | null>(null)

  useEffect(() => {
    fetchVisits()
  }, [])

  const fetchVisits = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/carefusion/patient/visits', {
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch visit history')
      }
      
      const data = await response.json()
      setVisits(data.visits || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
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

  const toggleExpanded = (visitId: string) => {
    setExpandedVisit(expandedVisit === visitId ? null : visitId)
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
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-cyan-500 to-blue-500 bg-clip-text text-transparent">
            Visit History
          </h1>
          <p className="text-zinc-400">Your complete medical visit records</p>
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

        {/* Visits List */}
        {!loading && !error && (
          <>
            {visits.length === 0 ? (
              <div className="text-center py-12 bg-zinc-900 border border-zinc-800 rounded-xl">
                <p className="text-zinc-500 text-lg mb-4">No visit history found</p>
                <button
                  onClick={() => router.push('/portals/carefusion/patient/appointments/book')}
                  className="text-cyan-400 hover:text-cyan-300"
                >
                  Schedule your first appointment
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {visits.map((visit) => (
                  <div
                    key={visit.id}
                    className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden hover:border-cyan-600 transition-all"
                  >
                    {/* Visit Header */}
                    <div
                      onClick={() => toggleExpanded(visit.id)}
                      className="p-6 cursor-pointer"
                    >
                      <div className="flex flex-col md:flex-row md:items-center gap-4">
                        {/* Date */}
                        <div className="flex-shrink-0 text-center md:text-left">
                          <div className="text-2xl font-bold text-cyan-400">
                            {new Date(visit.date).getDate()}
                          </div>
                          <div className="text-sm text-zinc-400">
                            {new Date(visit.date).toLocaleDateString('en-US', { 
                              month: 'short',
                              year: 'numeric'
                            })}
                          </div>
                        </div>

                        {/* Visit Info */}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xl">{getTypeIcon(visit.type)}</span>
                            <h3 className="text-xl font-semibold">{visit.providerName}</h3>
                          </div>
                          <p className="text-zinc-400 mb-1">{visit.providerSpecialty}</p>
                          <p className="text-zinc-500 text-sm">
                            <span className="font-medium text-zinc-400">Diagnosis:</span> {visit.diagnosis}
                          </p>
                        </div>

                        {/* Expand Icon */}
                        <div className="flex-shrink-0">
                          <div className="text-2xl text-cyan-400">
                            {expandedVisit === visit.id ? '▼' : '▶'}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {expandedVisit === visit.id && (
                      <div className="border-t border-zinc-800 p-6 bg-zinc-900/50">
                        <div className="space-y-6">
                          {/* Prescriptions */}
                          {visit.prescriptions.length > 0 && (
                            <div>
                              <h4 className="font-semibold text-cyan-400 mb-3 flex items-center gap-2">
                                💊 Prescriptions
                              </h4>
                              <ul className="space-y-2">
                                {visit.prescriptions.map((prescription, index) => (
                                  <li key={index} className="flex items-start gap-2 text-zinc-300">
                                    <span className="text-cyan-400">•</span>
                                    {prescription}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Visit Notes */}
                          {visit.notes && (
                            <div>
                              <h4 className="font-semibold text-cyan-400 mb-3 flex items-center gap-2">
                                📝 Visit Notes
                              </h4>
                              <p className="text-zinc-300 leading-relaxed">{visit.notes}</p>
                            </div>
                          )}

                          {/* Follow-up */}
                          {visit.followUpRequired && (
                            <div className="bg-yellow-900/20 border border-yellow-800 rounded-lg p-4">
                              <p className="text-yellow-400 flex items-center gap-2">
                                <span>⚠️</span>
                                Follow-up appointment recommended
                              </p>
                            </div>
                          )}

                          {/* Documents */}
                          {visit.documentIds && visit.documentIds.length > 0 && (
                            <div>
                              <h4 className="font-semibold text-cyan-400 mb-3 flex items-center gap-2">
                                📄 Related Documents
                              </h4>
                              <div className="flex flex-wrap gap-2">
                                {visit.documentIds.map((docId, index) => (
                                  <button
                                    key={docId}
                                    onClick={() => router.push(`/portals/carefusion/patient/medical-records?doc=${docId}`)}
                                    className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-sm transition-colors"
                                  >
                                    Document {index + 1}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Actions */}
                          <div className="flex flex-wrap gap-3 pt-4 border-t border-zinc-800">
                            <button
                              onClick={() => router.push(`/portals/carefusion/patient/providers/${visit.providerId}`)}
                              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm font-medium transition-colors"
                            >
                              View Provider
                            </button>
                            {visit.followUpRequired && (
                              <button
                                onClick={() => router.push(`/portals/carefusion/patient/appointments/book?providerId=${visit.providerId}`)}
                                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
                              >
                                Schedule Follow-up
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
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
