"use client"

import { useState, useEffect } from "react"
import Link from "next/link"

interface Patient {
  id: string
  firstName: string
  lastName: string
  dateOfBirth: string
  gender: string
  mrn: string
  phone: string
  email: string
  lastVisit?: string
  status: string
}

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [filterStatus, setFilterStatus] = useState("all")

  useEffect(() => {
    fetchPatients()
  }, [])

  const fetchPatients = async () => {
    try {
      setLoading(true)
      const response = await fetch("/api/carefusion/provider/patients", {
        credentials: "include"
      })
      
      if (!response.ok) throw new Error("Failed to fetch patients")
      
      const data = await response.json()
      setPatients(data.patients || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error loading patients")
    } finally {
      setLoading(false)
    }
  }

  const filteredPatients = patients.filter(patient => {
    const matchesSearch = 
      patient.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.lastName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.mrn.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesStatus = filterStatus === "all" || patient.status === filterStatus
    
    return matchesSearch && matchesStatus
  })

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-400">Loading patients...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
            Patient List
          </h1>
          <p className="text-zinc-400">Manage and view patient records</p>
        </div>

        {error && (
          <div className="bg-red-950/50 border border-red-800 text-red-300 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search by name or MRN..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-zinc-950 border-b border-zinc-800">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">MRN</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Patient Name</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">DOB</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Gender</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Contact</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Last Visit</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Status</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {filteredPatients.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-zinc-500">
                    No patients found
                  </td>
                </tr>
              ) : (
                filteredPatients.map((patient) => (
                  <tr key={patient.id} className="hover:bg-zinc-800/50 transition">
                    <td className="px-6 py-4 text-sm font-mono text-zinc-400">{patient.mrn}</td>
                    <td className="px-6 py-4">
                      <div className="font-medium">{patient.firstName} {patient.lastName}</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-zinc-400">{patient.dateOfBirth}</td>
                    <td className="px-6 py-4 text-sm text-zinc-400">{patient.gender}</td>
                    <td className="px-6 py-4 text-sm text-zinc-400">
                      <div>{patient.phone}</div>
                      <div className="text-xs text-zinc-500">{patient.email}</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-zinc-400">
                      {patient.lastVisit || "No visits"}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        patient.status === "active" 
                          ? "bg-green-950/50 text-green-400 border border-green-800"
                          : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                      }`}>
                        {patient.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        href={`/portals/carefusion/provider/patients/${patient.id}`}
                        className="text-purple-400 hover:text-purple-300 text-sm font-medium"
                      >
                        View Details
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
