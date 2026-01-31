"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"

interface VisitDetail {
  id: string
  patientId: string
  patientName: string
  patientMrn: string
  visitDate: string
  visitTime: string
  visitType: string
  chiefComplaint: string
  status: string
}

interface SOAPNote {
  subjective: string
  objective: string
  assessment: string
  plan: string
}

interface VitalSigns {
  temperature: string
  bloodPressure: string
  heartRate: string
  respiratoryRate: string
  oxygenSaturation: string
  weight: string
  height: string
}

interface Diagnosis {
  id?: string
  code: string
  description: string
  type: string
}

export default function VisitDetailPage() {
  const params = useParams()
  const router = useRouter()
  const visitId = params.id as string
  
  const [visit, setVisit] = useState<VisitDetail | null>(null)
  const [soapNote, setSoapNote] = useState<SOAPNote>({
    subjective: "",
    objective: "",
    assessment: "",
    plan: ""
  })
  const [vitals, setVitals] = useState<VitalSigns>({
    temperature: "",
    bloodPressure: "",
    heartRate: "",
    respiratoryRate: "",
    oxygenSaturation: "",
    weight: "",
    height: ""
  })
  const [diagnoses, setDiagnoses] = useState<Diagnosis[]>([])
  const [newDiagnosis, setNewDiagnosis] = useState<Diagnosis>({
    code: "",
    description: "",
    type: "primary"
  })
  const [activeSection, setActiveSection] = useState("soap")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchVisitData()
  }, [visitId])

  const fetchVisitData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/carefusion/provider/visits/${visitId}`, {
        credentials: "include"
      })
      
      if (!response.ok) throw new Error("Failed to fetch visit data")
      
      const data = await response.json()
      setVisit(data.visit)
      if (data.soapNote) setSoapNote(data.soapNote)
      if (data.vitals) setVitals(data.vitals)
      if (data.diagnoses) setDiagnoses(data.diagnoses)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error loading visit data")
    } finally {
      setLoading(false)
    }
  }

  const handleSaveSOAP = async () => {
    try {
      setSaving(true)
      const response = await fetch(`/api/carefusion/provider/visits/${visitId}/soap`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(soapNote)
      })

      if (!response.ok) throw new Error("Failed to save SOAP note")
      
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error saving SOAP note")
    } finally {
      setSaving(false)
    }
  }

  const handleSaveVitals = async () => {
    try {
      setSaving(true)
      const response = await fetch(`/api/carefusion/provider/visits/${visitId}/vitals`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(vitals)
      })

      if (!response.ok) throw new Error("Failed to save vital signs")
      
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error saving vital signs")
    } finally {
      setSaving(false)
    }
  }

  const handleAddDiagnosis = async () => {
    try {
      const response = await fetch(`/api/carefusion/provider/visits/${visitId}/diagnoses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(newDiagnosis)
      })

      if (!response.ok) throw new Error("Failed to add diagnosis")

      await fetchVisitData()
      setNewDiagnosis({ code: "", description: "", type: "primary" })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error adding diagnosis")
    }
  }

  const handleCompleteVisit = async () => {
    try {
      setSaving(true)
      const response = await fetch(`/api/carefusion/provider/visits/${visitId}/complete`, {
        method: "POST",
        credentials: "include"
      })

      if (!response.ok) throw new Error("Failed to complete visit")

      router.push("/portals/carefusion/provider/visits")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error completing visit")
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-400">Loading visit documentation...</p>
        </div>
      </div>
    )
  }

  if (error && !visit) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-950/50 border border-red-800 text-red-300 px-4 py-3 rounded-lg">
            {error}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <Link href="/portals/carefusion/provider/visits" className="text-purple-400 hover:text-purple-300 text-sm">
            ← Back to Visits
          </Link>
        </div>

        {visit && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-6">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-3xl font-bold mb-2">{visit.patientName}</h1>
                <div className="flex items-center gap-4 text-sm text-zinc-400">
                  <span>MRN: {visit.patientMrn}</span>
                  <span>•</span>
                  <span>{visit.visitDate} at {visit.visitTime}</span>
                  <span>•</span>
                  <span className="capitalize">{visit.visitType}</span>
                </div>
                <div className="mt-2 text-sm">
                  <span className="text-zinc-400">Chief Complaint:</span>
                  <span className="ml-2 font-medium">{visit.chiefComplaint}</span>
                </div>
              </div>
              <Link
                href={`/portals/carefusion/provider/patients/${visit.patientId}`}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-sm font-medium transition"
              >
                View Patient Chart
              </Link>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-950/50 border border-red-800 text-red-300 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="mb-6">
          <div className="flex gap-2 border-b border-zinc-800">
            {["soap", "vitals", "diagnoses", "orders"].map((section) => (
              <button
                key={section}
                onClick={() => setActiveSection(section)}
                className={`px-6 py-3 font-medium capitalize transition ${
                  activeSection === section
                    ? "text-purple-400 border-b-2 border-purple-400"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {section}
              </button>
            ))}
          </div>
        </div>

        {activeSection === "soap" && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-6">SOAP Note Documentation</h2>
            
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-zinc-300 mb-2">
                  Subjective (Chief Complaint, HPI, Review of Systems)
                </label>
                <textarea
                  value={soapNote.subjective}
                  onChange={(e) => setSoapNote({ ...soapNote, subjective: e.target.value })}
                  rows={6}
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                  placeholder="Patient reports..."
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-zinc-300 mb-2">
                  Objective (Physical Exam Findings, Lab Results)
                </label>
                <textarea
                  value={soapNote.objective}
                  onChange={(e) => setSoapNote({ ...soapNote, objective: e.target.value })}
                  rows={6}
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                  placeholder="On examination..."
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-zinc-300 mb-2">
                  Assessment (Diagnosis, Clinical Impression)
                </label>
                <textarea
                  value={soapNote.assessment}
                  onChange={(e) => setSoapNote({ ...soapNote, assessment: e.target.value })}
                  rows={4}
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                  placeholder="Clinical assessment..."
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-zinc-300 mb-2">
                  Plan (Treatment Plan, Follow-up, Patient Education)
                </label>
                <textarea
                  value={soapNote.plan}
                  onChange={(e) => setSoapNote({ ...soapNote, plan: e.target.value })}
                  rows={6}
                  className="w-full px-4 py-3 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                  placeholder="Treatment plan includes..."
                />
              </div>

              <button
                onClick={handleSaveSOAP}
                disabled={saving}
                className="w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition"
              >
                {saving ? "Saving..." : "Save SOAP Note"}
              </button>
            </div>
          </div>
        )}

        {activeSection === "vitals" && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-6">Vital Signs</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Temperature (°F)</label>
                <input
                  type="text"
                  value={vitals.temperature}
                  onChange={(e) => setVitals({ ...vitals, temperature: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="98.6"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Blood Pressure (mmHg)</label>
                <input
                  type="text"
                  value={vitals.bloodPressure}
                  onChange={(e) => setVitals({ ...vitals, bloodPressure: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="120/80"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Heart Rate (bpm)</label>
                <input
                  type="text"
                  value={vitals.heartRate}
                  onChange={(e) => setVitals({ ...vitals, heartRate: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="72"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Respiratory Rate (bpm)</label>
                <input
                  type="text"
                  value={vitals.respiratoryRate}
                  onChange={(e) => setVitals({ ...vitals, respiratoryRate: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="16"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">O2 Saturation (%)</label>
                <input
                  type="text"
                  value={vitals.oxygenSaturation}
                  onChange={(e) => setVitals({ ...vitals, oxygenSaturation: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="98"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Weight (lbs)</label>
                <input
                  type="text"
                  value={vitals.weight}
                  onChange={(e) => setVitals({ ...vitals, weight: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="150"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2">Height (in)</label>
                <input
                  type="text"
                  value={vitals.height}
                  onChange={(e) => setVitals({ ...vitals, height: e.target.value })}
                  className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="68"
                />
              </div>
            </div>

            <button
              onClick={handleSaveVitals}
              disabled={saving}
              className="w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition"
            >
              {saving ? "Saving..." : "Save Vital Signs"}
            </button>
          </div>
        )}

        {activeSection === "diagnoses" && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="p-6 border-b border-zinc-800">
              <h2 className="text-xl font-semibold mb-4">Diagnoses</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <input
                  type="text"
                  value={newDiagnosis.code}
                  onChange={(e) => setNewDiagnosis({ ...newDiagnosis, code: e.target.value })}
                  className="px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="ICD-10 Code"
                />
                <input
                  type="text"
                  value={newDiagnosis.description}
                  onChange={(e) => setNewDiagnosis({ ...newDiagnosis, description: e.target.value })}
                  className="px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Diagnosis Description"
                />
                <div className="flex gap-2">
                  <select
                    value={newDiagnosis.type}
                    onChange={(e) => setNewDiagnosis({ ...newDiagnosis, type: e.target.value })}
                    className="flex-1 px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="primary">Primary</option>
                    <option value="secondary">Secondary</option>
                  </select>
                  <button
                    onClick={handleAddDiagnosis}
                    className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>

            <table className="w-full">
              <thead className="bg-zinc-950 border-b border-zinc-800">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Code</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Description</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-zinc-300">Type</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {diagnoses.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="px-6 py-8 text-center text-zinc-500">
                      No diagnoses added
                    </td>
                  </tr>
                ) : (
                  diagnoses.map((diagnosis, index) => (
                    <tr key={index} className="hover:bg-zinc-800/50">
                      <td className="px-6 py-4 font-mono text-sm">{diagnosis.code}</td>
                      <td className="px-6 py-4">{diagnosis.description}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          diagnosis.type === "primary"
                            ? "bg-purple-950/50 text-purple-400 border border-purple-800"
                            : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                        }`}>
                          {diagnosis.type}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeSection === "orders" && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4">Orders & Prescriptions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link
                href={`/portals/carefusion/provider/prescriptions?visitId=${visitId}`}
                className="p-6 bg-zinc-950 hover:bg-zinc-800 border border-zinc-700 rounded-lg transition"
              >
                <h3 className="text-lg font-semibold mb-2">E-Prescribing</h3>
                <p className="text-sm text-zinc-400">Order medications for this visit</p>
              </Link>
              <div className="p-6 bg-zinc-950 border border-zinc-700 rounded-lg opacity-50">
                <h3 className="text-lg font-semibold mb-2">Lab Orders</h3>
                <p className="text-sm text-zinc-400">Order laboratory tests (Coming soon)</p>
              </div>
              <div className="p-6 bg-zinc-950 border border-zinc-700 rounded-lg opacity-50">
                <h3 className="text-lg font-semibold mb-2">Imaging Orders</h3>
                <p className="text-sm text-zinc-400">Order radiology studies (Coming soon)</p>
              </div>
              <div className="p-6 bg-zinc-950 border border-zinc-700 rounded-lg opacity-50">
                <h3 className="text-lg font-semibold mb-2">Referrals</h3>
                <p className="text-sm text-zinc-400">Refer to specialists (Coming soon)</p>
              </div>
            </div>
          </div>
        )}

        <div className="mt-6 flex justify-end gap-4">
          <button
            onClick={() => router.push("/portals/carefusion/provider/visits")}
            className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg font-medium transition"
          >
            Save & Exit
          </button>
          <button
            onClick={handleCompleteVisit}
            disabled={saving}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition"
          >
            {saving ? "Completing..." : "Complete Visit"}
          </button>
        </div>
      </div>
    </div>
  )
}
