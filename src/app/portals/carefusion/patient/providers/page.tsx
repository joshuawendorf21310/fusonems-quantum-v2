"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface Provider {
  id: string
  name: string
  specialty: string
  credentials: string
  photoUrl?: string
  rating: number
  yearsExperience: number
  acceptingNewPatients: boolean
}

export default function ProvidersPage() {
  const router = useRouter()
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedSpecialty, setSelectedSpecialty] = useState<string>('all')

  const specialties = [
    'All Specialties',
    'Primary Care',
    'Cardiology',
    'Dermatology',
    'Endocrinology',
    'Gastroenterology',
    'Neurology',
    'Orthopedics',
    'Pediatrics',
    'Psychiatry',
    'Radiology'
  ]

  useEffect(() => {
    fetchProviders()
  }, [])

  const fetchProviders = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/carefusion/patient/providers', {
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch providers')
      }
      
      const data = await response.json()
      setProviders(data.providers || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const filteredProviders = providers.filter(provider => {
    const matchesSearch = provider.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         provider.specialty.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesSpecialty = selectedSpecialty === 'all' || 
                            provider.specialty.toLowerCase() === selectedSpecialty.toLowerCase()
    return matchesSearch && matchesSpecialty
  })

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-7xl mx-auto p-6 md:p-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/portals/carefusion/patient/dashboard')}
            className="text-cyan-400 hover:text-cyan-300 mb-4 flex items-center gap-2"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-cyan-500 to-blue-500 bg-clip-text text-transparent">
            Find a Provider
          </h1>
          <p className="text-zinc-400">Search our network of healthcare providers</p>
        </div>

        {/* Search and Filter */}
        <div className="mb-8 space-y-4">
          <input
            type="text"
            placeholder="Search by name or specialty..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
          
          <div className="flex gap-2 flex-wrap">
            {specialties.map((specialty) => (
              <button
                key={specialty}
                onClick={() => setSelectedSpecialty(specialty === 'All Specialties' ? 'all' : specialty)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  (selectedSpecialty === 'all' && specialty === 'All Specialties') ||
                  selectedSpecialty === specialty
                    ? 'bg-cyan-600 text-white'
                    : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800 border border-zinc-800'
                }`}
              >
                {specialty}
              </button>
            ))}
          </div>
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

        {/* Providers Grid */}
        {!loading && !error && (
          <>
            <div className="mb-4 text-zinc-400">
              {filteredProviders.length} provider{filteredProviders.length !== 1 ? 's' : ''} found
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredProviders.map((provider) => (
                <div
                  key={provider.id}
                  onClick={() => router.push(`/portals/carefusion/patient/providers/${provider.id}`)}
                  className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-cyan-600 transition-all cursor-pointer group"
                >
                  {/* Provider Photo */}
                  <div className="flex items-start gap-4 mb-4">
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-2xl font-bold flex-shrink-0">
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
                    <div className="flex-1 min-w-0">
                      <h3 className="text-xl font-semibold text-zinc-100 group-hover:text-cyan-400 transition-colors truncate">
                        {provider.name}
                      </h3>
                      <p className="text-sm text-zinc-500">{provider.credentials}</p>
                    </div>
                  </div>

                  {/* Specialty Badge */}
                  <div className="mb-4">
                    <span className="inline-block px-3 py-1 bg-cyan-600/20 text-cyan-400 rounded-full text-sm font-medium">
                      {provider.specialty}
                    </span>
                  </div>

                  {/* Provider Info */}
                  <div className="space-y-2 text-sm text-zinc-400 mb-4">
                    <div className="flex items-center gap-2">
                      <span className="text-yellow-500">★</span>
                      <span>{provider.rating.toFixed(1)} rating</span>
                    </div>
                    <div>
                      {provider.yearsExperience} years experience
                    </div>
                    <div className={provider.acceptingNewPatients ? 'text-green-400' : 'text-red-400'}>
                      {provider.acceptingNewPatients ? '✓ Accepting new patients' : '✗ Not accepting new patients'}
                    </div>
                  </div>

                  {/* Action Button */}
                  <button className="w-full py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-medium transition-colors">
                    View Profile
                  </button>
                </div>
              ))}
            </div>

            {filteredProviders.length === 0 && (
              <div className="text-center py-12">
                <p className="text-zinc-500 text-lg">No providers found matching your criteria</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
