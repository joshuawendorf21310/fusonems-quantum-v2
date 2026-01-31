"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"

interface PatientDetail {
  id: string
  firstName: string
  lastName: string
  dateOfBirth: string
  gender: string
  mrn: string
  phone: string
  email: string
  address: string
  insurance: string
  emergencyContact: string
  status: string
}

interface MedicalHistory {
  id: string
  condition: string
  diagnosedDate: string
  status: string
  notes: string
}

interface Allergy {
  id: string
  allergen: string
  reaction: string
  severity: string
  onsetDate: string
}

interface Medication {
  id: string
  name: string
  dosage: string
  frequency: string
  prescribedDate: string
  prescribedBy: string
  status: string
}

export default function PatientDetailPage() {
  const params = useParams()
  const patientId = params.id as string
  
  const [patient, setPatient] = useState<PatientDetail | null>(null)
  const [medicalHistory, setMedicalHistory] = useState<MedicalHistory[]>([])
  const [allergies, setAllergies] = useState<Allergy[]>([])
  const [medications, setMedications] = useState<Medication[]>([])
  const [activeTab, setActiveTab] = useState("overview")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPatientData()
  }, [patientId])

  const fetchPatientData = async () => {
    try {
      setLoading(true)
      const [patientRes, historyRes, allergiesRes, medsRes] = await Promise.all([
        fetch(`/api/carefusion/provider/patients/${patientId}`, { credentials: "include" }),
        fetch(`/api/carefusion/provider/patients/${patientId}/history`, { credentials: "include" }),
        fetch(`/api/carefusion/provider/patients/${patientId}/allergies`, { credentials: "include" }),
        fetch(`/api/carefusion/provider/patients/${patientId}/medications`, { credentials: "include" })
      ])

      if (!patientRes.ok) throw new Error("Failed to fetch patient data")

      const patientData = await patientRes.json()
      const historyData = await historyRes.json()
      const allergiesData = await allergiesRes.json()
      const medsData = await medsRes.json()

      setPatient(patientData.patient)
      setMedicalHistory(historyData.history || [])
      setAllergies(allergiesData.allergies || [])
      setMedications(medsData.medications || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error loading patient data")
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-400">Loading patient data...</p>
        </div>
      </div>
    )
  }

  if (error || !patient) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-950/50 border border-red-800 text-red-300 px-4 py-3 rounded-lg">
            {error || "Patient not found"}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <Link href="/portals/carefusion/provider/patients" className="text-purple-400 hover:text-purple-300 text-sm">
            ← Back to Patients
          </Link>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">
                {patient.firstName} {patient.lastName}
              </h1>
              <div className="flex items-center gap-4 text-sm text-zinc-400">
                <span>MRN: {patient.mrn}</span>
                <span>•</span>
                <span>DOB: {patient.dateOfBirth}</span>
                <span>•</span>
                <span>{patient.gender}</span>
              </div>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              patient.status === "active" 
                ? "bg-green-950/50 text-green-400 border border-green-800"
                : "bg-zinc-800 text-zinc-400 border border-zinc-700"
            }`}>
              {patient.status}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="text-sm font-semibold text-zinc-400 mb-2">Contact</h3>
              <div className="text-sm">
                <p>{patient.phone}</p>
                <p className="text-zinc-400">{patient.email}</p>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-zinc-400 mb-2">Address</h3>
              <p className="text-sm">{patient.address}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-zinc-400 mb-2">Insurance</h3>
              <p className="text-sm">{patient.insurance}</p>
            </div>
          </div>
        </div>

        <div className="mb-6">
          <div className="flex gap-2 border-b border-zinc-800">
            {["overview", "history", "allergies", "medications"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-3 font-medium capitalize transition ${
                  activeTab === tab
                    ? "text-purple-400 border-b-2 border-purple-400"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {activeTab === "overview" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
              <div className="space-y-3">
                <Link
                  href={`/portals/carefusion/provider/visits/new?patientId=${patientId}`}
                  className="block w-full px-4 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-center font-medium transition"
                >
                  Start New Visit
                </Link>
                <Link
                  href={`/portals/carefusion/provider/prescriptions?patientId=${patientId}`}
                  className="block w-full px-4 py-3 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-center font-medium transition"
                >
                  Prescribe Medication
                </Link>
                <Link
                  href={`/portals/carefusion/provider/appointments?patientId=${patientId}`}
                  className="block w-full px-4 py-3 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-center font-medium transition"
                >
                  Schedule Appointment
                </Link>
              </div>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <h2 className="text-xl font-semibold mb-4">Emergency Contact</h2>
              <p className="text-zinc-400">{patient.emergencyContact || "Not provided"}</p>
            </div>
          </div>
        )}

        {activeTab === "history" && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Medical History</h2>
              <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition">
                Add Condition
              </button>
            </div>
            <table className="w-full">
              <thead className="bg-zinc-950 border-b border-zinc-800">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Condition</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Diagnosed Date</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Status</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {medicalHistory.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-zinc-500">
                      No medical history recorded
                    </td>
                  </tr>
                ) : (
                  medicalHistory.map((item) => (
                    <tr key={item.id} className="hover:bg-zinc-800/50">
                      <td className="px-6 py-4 font-medium">{item.condition}</td>
                      <td className="px-6 py-4 text-sm text-zinc-400">{item.diagnosedDate}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          item.status === "active"
                            ? "bg-red-950/50 text-red-400 border border-red-800"
                            : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                        }`}>
                          {item.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-zinc-400">{item.notes}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === "allergies" && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Allergies</h2>
              <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition">
                Add Allergy
              </button>
            </div>
            <table className="w-full">
              <thead className="bg-zinc-950 border-b border-zinc-800">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Allergen</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Reaction</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Severity</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Onset Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {allergies.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-zinc-500">
                      No known allergies
                    </td>
                  </tr>
                ) : (
                  allergies.map((allergy) => (
                    <tr key={allergy.id} className="hover:bg-zinc-800/50">
                      <td className="px-6 py-4 font-medium">{allergy.allergen}</td>
                      <td className="px-6 py-4 text-sm text-zinc-400">{allergy.reaction}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          allergy.severity === "severe"
                            ? "bg-red-950/50 text-red-400 border border-red-800"
                            : allergy.severity === "moderate"
                            ? "bg-orange-950/50 text-orange-400 border border-orange-800"
                            : "bg-yellow-950/50 text-yellow-400 border border-yellow-800"
                        }`}>
                          {allergy.severity}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-zinc-400">{allergy.onsetDate}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === "medications" && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Current Medications</h2>
              <Link
                href={`/portals/carefusion/provider/prescriptions?patientId=${patientId}`}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition"
              >
                Prescribe Medication
              </Link>
            </div>
            <table className="w-full">
              <thead className="bg-zinc-950 border-b border-zinc-800">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Medication</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Dosage</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Frequency</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Prescribed By</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Date</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {medications.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-zinc-500">
                      No medications prescribed
                    </td>
                  </tr>
                ) : (
                  medications.map((med) => (
                    <tr key={med.id} className="hover:bg-zinc-800/50">
                      <td className="px-6 py-4 font-medium">{med.name}</td>
                      <td className="px-6 py-4 text-sm text-zinc-400">{med.dosage}</td>
                      <td className="px-6 py-4 text-sm text-zinc-400">{med.frequency}</td>
                      <td className="px-6 py-4 text-sm text-zinc-400">{med.prescribedBy}</td>
                      <td className="px-6 py-4 text-sm text-zinc-400">{med.prescribedDate}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          med.status === "active"
                            ? "bg-green-950/50 text-green-400 border border-green-800"
                            : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                        }`}>
                          {med.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
