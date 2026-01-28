"use client"

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"

interface Medication {
  name: string
  genericName: string
  strength: string
  form: string
}

interface Prescription {
  medicationName: string
  dosage: string
  frequency: string
  duration: string
  quantity: number
  refills: number
  instructions: string
  pharmacyId?: string
}

export default function PrescriptionsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const patientId = searchParams.get("patientId")
  const visitId = searchParams.get("visitId")

  const [searchTerm, setSearchTerm] = useState("")
  const [medications, setMedications] = useState<Medication[]>([])
  const [searching, setSearching] = useState(false)
  const [prescription, setPrescription] = useState<Prescription>({
    medicationName: "",
    dosage: "",
    frequency: "once daily",
    duration: "30 days",
    quantity: 30,
    refills: 0,
    instructions: "",
    pharmacyId: ""
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSearchMedication = async () => {
    if (!searchTerm.trim()) return

    try {
      setSearching(true)
      const response = await fetch(`/api/carefusion/provider/medications/search?q=${encodeURIComponent(searchTerm)}`, {
        credentials: "include"
      })
      
      if (!response.ok) throw new Error("Failed to search medications")
      
      const data = await response.json()
      setMedications(data.medications || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error searching medications")
    } finally {
      setSearching(false)
    }
  }

  const handleSelectMedication = (med: Medication) => {
    setPrescription({
      ...prescription,
      medicationName: `${med.name} ${med.strength} ${med.form}`
    })
    setMedications([])
    setSearchTerm("")
  }

  const handleSubmitPrescription = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch("/api/carefusion/provider/prescriptions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          ...prescription,
          patientId,
          visitId
        })
      })

      if (!response.ok) throw new Error("Failed to submit prescription")

      setSuccess(true)
      
      setTimeout(() => {
        if (visitId) {
          router.push(`/portals/carefusion/provider/visits/${visitId}`)
        } else if (patientId) {
          router.push(`/portals/carefusion/provider/patients/${patientId}`)
        } else {
          router.push("/portals/carefusion/provider/dashboard")
        }
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error submitting prescription")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
            E-Prescribing
          </h1>
          <p className="text-zinc-400">Prescribe medications electronically</p>
        </div>

        {error && (
          <div className="bg-red-950/50 border border-red-800 text-red-300 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-green-950/50 border border-green-800 text-green-300 px-4 py-3 rounded-lg mb-6">
            Prescription submitted successfully!
          </div>
        )}

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Search Medication</h2>
          
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSearchMedication()}
              className="flex-1 px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="Search by medication name..."
            />
            <button
              onClick={handleSearchMedication}
              disabled={searching}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition"
            >
              {searching ? "Searching..." : "Search"}
            </button>
          </div>

          {medications.length > 0 && (
            <div className="bg-zinc-950 border border-zinc-700 rounded-lg max-h-64 overflow-y-auto">
              {medications.map((med, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectMedication(med)}
                  className="w-full px-4 py-3 text-left hover:bg-zinc-800 transition border-b border-zinc-800 last:border-b-0"
                >
                  <div className="font-medium">{med.name}</div>
                  <div className="text-sm text-zinc-400">
                    {med.genericName} - {med.strength} {med.form}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Prescription Details</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">Medication</label>
              <input
                type="text"
                value={prescription.medicationName}
                onChange={(e) => setPrescription({ ...prescription, medicationName: e.target.value })}
                className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="Select from search or enter manually"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Dosage</label>
                <input
                  type="text"
                  value={prescription.dosage}
                  onChange={(e) => setPrescription({ ...prescription, dosage: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="e.g., 10 mg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Frequency</label>
                <select
                  value={prescription.frequency}
                  onChange={(e) => setPrescription({ ...prescription, frequency: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="once daily">Once daily</option>
                  <option value="twice daily">Twice daily</option>
                  <option value="three times daily">Three times daily</option>
                  <option value="four times daily">Four times daily</option>
                  <option value="every 4 hours">Every 4 hours</option>
                  <option value="every 6 hours">Every 6 hours</option>
                  <option value="every 8 hours">Every 8 hours</option>
                  <option value="every 12 hours">Every 12 hours</option>
                  <option value="as needed">As needed</option>
                  <option value="at bedtime">At bedtime</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Duration</label>
                <select
                  value={prescription.duration}
                  onChange={(e) => setPrescription({ ...prescription, duration: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="7 days">7 days</option>
                  <option value="14 days">14 days</option>
                  <option value="30 days">30 days</option>
                  <option value="60 days">60 days</option>
                  <option value="90 days">90 days</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Quantity</label>
                <input
                  type="number"
                  value={prescription.quantity}
                  onChange={(e) => setPrescription({ ...prescription, quantity: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  min="1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Refills</label>
                <input
                  type="number"
                  value={prescription.refills}
                  onChange={(e) => setPrescription({ ...prescription, refills: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  min="0"
                  max="12"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">Instructions for Patient</label>
              <textarea
                value={prescription.instructions}
                onChange={(e) => setPrescription({ ...prescription, instructions: e.target.value })}
                rows={3}
                className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                placeholder="Take with food, avoid alcohol, etc."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-400 mb-2">Pharmacy (Optional)</label>
              <select
                value={prescription.pharmacyId}
                onChange={(e) => setPrescription({ ...prescription, pharmacyId: e.target.value })}
                className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Use patient's preferred pharmacy</option>
                <option value="cvs-1">CVS Pharmacy - Main St</option>
                <option value="walgreens-1">Walgreens - Oak Ave</option>
                <option value="walmart-1">Walmart Pharmacy - Center Dr</option>
              </select>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-4">
          <button
            onClick={() => router.back()}
            className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg font-medium transition"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmitPrescription}
            disabled={loading || !prescription.medicationName || !prescription.dosage}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition"
          >
            {loading ? "Submitting..." : "Submit Prescription"}
          </button>
        </div>
      </div>
    </div>
  )
}
