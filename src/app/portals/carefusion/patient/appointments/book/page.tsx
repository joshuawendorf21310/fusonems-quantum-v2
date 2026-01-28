"use client"

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

interface Provider {
  id: string
  name: string
  specialty: string
  photoUrl?: string
}

interface TimeSlot {
  date: string
  time: string
  available: boolean
}

export default function BookAppointmentPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const preselectedProviderId = searchParams.get('providerId')

  const [providers, setProviders] = useState<Provider[]>([])
  const [selectedProviderId, setSelectedProviderId] = useState<string>(preselectedProviderId || '')
  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(null)
  const [appointmentType, setAppointmentType] = useState<'video' | 'phone' | 'in-person'>('video')
  const [reason, setReason] = useState('')
  const [selectedDate, setSelectedDate] = useState('')
  const [selectedTime, setSelectedTime] = useState('')
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [step, setStep] = useState(1)

  useEffect(() => {
    fetchProviders()
  }, [])

  useEffect(() => {
    if (selectedProviderId) {
      const provider = providers.find(p => p.id === selectedProviderId)
      setSelectedProvider(provider || null)
      if (provider && step >= 2) {
        fetchAvailableSlots()
      }
    }
  }, [selectedProviderId, providers])

  const fetchProviders = async () => {
    try {
      const response = await fetch('/api/carefusion/patient/providers', {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        setProviders(data.providers || [])
      }
    } catch (err) {
      console.error('Failed to fetch providers:', err)
    }
  }

  const fetchAvailableSlots = async () => {
    if (!selectedProviderId) return

    try {
      setLoading(true)
      const response = await fetch(
        `/api/carefusion/patient/appointments/availability?providerId=${selectedProviderId}&type=${appointmentType}`,
        { credentials: 'include' }
      )
      
      if (!response.ok) {
        throw new Error('Failed to fetch available slots')
      }
      
      const data = await response.json()
      setAvailableSlots(data.slots || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleBookAppointment = async () => {
    if (!selectedProviderId || !selectedDate || !selectedTime || !reason) {
      setError('Please fill in all required fields')
      return
    }

    try {
      setLoading(true)
      const response = await fetch('/api/carefusion/patient/appointments/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          providerId: selectedProviderId,
          date: selectedDate,
          time: selectedTime,
          type: appointmentType,
          reason
        })
      })
      
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Failed to book appointment')
      }
      
      const data = await response.json()
      router.push(`/portals/carefusion/patient/appointments/${data.appointmentId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const getNextSevenDays = () => {
    const days = []
    for (let i = 0; i < 7; i++) {
      const date = new Date()
      date.setDate(date.getDate() + i)
      days.push(date)
    }
    return days
  }

  const getTimeSlotsForDate = (date: string) => {
    return availableSlots.filter(slot => slot.date === date && slot.available)
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-4xl mx-auto p-6 md:p-8">
        {/* Header */}
        <button
          onClick={() => router.push('/portals/carefusion/patient/appointments')}
          className="text-cyan-400 hover:text-cyan-300 mb-6 flex items-center gap-2"
        >
          ← Back to Appointments
        </button>

        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-cyan-500 to-blue-500 bg-clip-text text-transparent">
          Book Appointment
        </h1>
        <p className="text-zinc-400 mb-8">Schedule your healthcare visit</p>

        {/* Progress Steps */}
        <div className="flex items-center gap-4 mb-8">
          {[1, 2, 3, 4].map((s) => (
            <div key={s} className="flex items-center flex-1">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                  step >= s ? 'bg-cyan-600 text-white' : 'bg-zinc-800 text-zinc-500'
                }`}
              >
                {s}
              </div>
              {s < 4 && (
                <div className={`flex-1 h-1 ${step > s ? 'bg-cyan-600' : 'bg-zinc-800'}`}></div>
              )}
            </div>
          ))}
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 mb-6">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Step 1: Select Provider */}
        {step === 1 && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-2xl font-bold mb-4">Select Provider</h2>
            <div className="space-y-3">
              {providers.map((provider) => (
                <div
                  key={provider.id}
                  onClick={() => setSelectedProviderId(provider.id)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedProviderId === provider.id
                      ? 'border-cyan-600 bg-cyan-600/10'
                      : 'border-zinc-800 hover:border-zinc-700'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-lg font-bold flex-shrink-0">
                      {provider.photoUrl ? (
                        <img src={provider.photoUrl} alt={provider.name} className="w-full h-full rounded-full object-cover" />
                      ) : (
                        provider.name.split(' ').map(n => n[0]).join('')
                      )}
                    </div>
                    <div>
                      <div className="font-semibold">{provider.name}</div>
                      <div className="text-sm text-zinc-400">{provider.specialty}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <button
              onClick={() => setStep(2)}
              disabled={!selectedProviderId}
              className="mt-6 w-full py-3 bg-cyan-600 hover:bg-cyan-700 disabled:bg-zinc-800 disabled:text-zinc-500 text-white rounded-lg font-medium transition-colors"
            >
              Continue
            </button>
          </div>
        )}

        {/* Step 2: Select Type & Reason */}
        {step === 2 && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-2xl font-bold mb-4">Appointment Details</h2>
            
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Appointment Type</label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: 'video', label: 'Video Call', icon: '📹' },
                  { value: 'phone', label: 'Phone Call', icon: '📞' },
                  { value: 'in-person', label: 'In-Person', icon: '🏥' }
                ].map((type) => (
                  <button
                    key={type.value}
                    onClick={() => setAppointmentType(type.value as any)}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      appointmentType === type.value
                        ? 'border-cyan-600 bg-cyan-600/10'
                        : 'border-zinc-800 hover:border-zinc-700'
                    }`}
                  >
                    <div className="text-2xl mb-2">{type.icon}</div>
                    <div className="text-sm font-medium">{type.label}</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Reason for Visit</label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Please describe the reason for your appointment..."
                rows={4}
                className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setStep(1)}
                className="flex-1 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-medium transition-colors"
              >
                Back
              </button>
              <button
                onClick={() => {
                  setStep(3)
                  fetchAvailableSlots()
                }}
                disabled={!reason}
                className="flex-1 py-3 bg-cyan-600 hover:bg-cyan-700 disabled:bg-zinc-800 disabled:text-zinc-500 text-white rounded-lg font-medium transition-colors"
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Select Date & Time */}
        {step === 3 && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-2xl font-bold mb-4">Select Date & Time</h2>
            
            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
              </div>
            ) : (
              <>
                <div className="mb-6">
                  <label className="block text-sm font-medium mb-3">Select Date</label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {getNextSevenDays().map((date) => {
                      const dateStr = date.toISOString().split('T')[0]
                      const slotsAvailable = getTimeSlotsForDate(dateStr).length
                      
                      return (
                        <button
                          key={dateStr}
                          onClick={() => setSelectedDate(dateStr)}
                          disabled={slotsAvailable === 0}
                          className={`p-4 rounded-lg border-2 transition-all ${
                            selectedDate === dateStr
                              ? 'border-cyan-600 bg-cyan-600/10'
                              : slotsAvailable > 0
                              ? 'border-zinc-800 hover:border-zinc-700'
                              : 'border-zinc-800 opacity-50 cursor-not-allowed'
                          }`}
                        >
                          <div className="text-sm text-zinc-400">
                            {date.toLocaleDateString('en-US', { weekday: 'short' })}
                          </div>
                          <div className="text-lg font-bold">
                            {date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          </div>
                          <div className="text-xs text-zinc-500 mt-1">
                            {slotsAvailable} slots
                          </div>
                        </button>
                      )
                    })}
                  </div>
                </div>

                {selectedDate && (
                  <div className="mb-6">
                    <label className="block text-sm font-medium mb-3">Select Time</label>
                    <div className="grid grid-cols-3 md:grid-cols-4 gap-3">
                      {getTimeSlotsForDate(selectedDate).map((slot) => (
                        <button
                          key={slot.time}
                          onClick={() => setSelectedTime(slot.time)}
                          className={`p-3 rounded-lg border-2 transition-all ${
                            selectedTime === slot.time
                              ? 'border-cyan-600 bg-cyan-600/10'
                              : 'border-zinc-800 hover:border-zinc-700'
                          }`}
                        >
                          {slot.time}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setStep(2)}
                className="flex-1 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-medium transition-colors"
              >
                Back
              </button>
              <button
                onClick={() => setStep(4)}
                disabled={!selectedDate || !selectedTime}
                className="flex-1 py-3 bg-cyan-600 hover:bg-cyan-700 disabled:bg-zinc-800 disabled:text-zinc-500 text-white rounded-lg font-medium transition-colors"
              >
                Review Booking
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Confirm */}
        {step === 4 && selectedProvider && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-2xl font-bold mb-6">Confirm Appointment</h2>
            
            <div className="space-y-4 mb-6">
              <div className="flex justify-between py-3 border-b border-zinc-800">
                <span className="text-zinc-400">Provider</span>
                <span className="font-medium">{selectedProvider.name}</span>
              </div>
              <div className="flex justify-between py-3 border-b border-zinc-800">
                <span className="text-zinc-400">Specialty</span>
                <span className="font-medium">{selectedProvider.specialty}</span>
              </div>
              <div className="flex justify-between py-3 border-b border-zinc-800">
                <span className="text-zinc-400">Type</span>
                <span className="font-medium capitalize">{appointmentType}</span>
              </div>
              <div className="flex justify-between py-3 border-b border-zinc-800">
                <span className="text-zinc-400">Date</span>
                <span className="font-medium">
                  {new Date(selectedDate).toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </span>
              </div>
              <div className="flex justify-between py-3 border-b border-zinc-800">
                <span className="text-zinc-400">Time</span>
                <span className="font-medium">{selectedTime}</span>
              </div>
              <div className="py-3">
                <div className="text-zinc-400 mb-2">Reason</div>
                <div className="text-zinc-300">{reason}</div>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setStep(3)}
                className="flex-1 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-medium transition-colors"
              >
                Back
              </button>
              <button
                onClick={handleBookAppointment}
                disabled={loading}
                className="flex-1 py-3 bg-green-600 hover:bg-green-700 disabled:bg-zinc-800 disabled:text-zinc-500 text-white rounded-lg font-medium transition-colors"
              >
                {loading ? 'Booking...' : 'Confirm Appointment'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
