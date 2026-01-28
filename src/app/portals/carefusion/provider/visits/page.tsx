"use client"

import { useState, useEffect } from "react"
import Link from "next/link"

interface Visit {
  id: string
  patientId: string
  patientName: string
  patientMrn: string
  visitDate: string
  visitTime: string
  visitType: string
  chiefComplaint: string
  status: string
  providerId: string
  providerName: string
}

export default function VisitsPage() {
  const [visits, setVisits] = useState<Visit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterStatus, setFilterStatus] = useState("all")
  const [searchTerm, setSearchTerm] = useState("")

  useEffect(() => {
    fetchVisits()
  }, [])

  const fetchVisits = async () => {
    try {
      setLoading(true)
      const response = await fetch("/api/carefusion/provider/visits", {
        credentials: "include"
      })
      
      if (!response.ok) throw new Error("Failed to fetch visits")
      
      const data = await response.json()
      setVisits(data.visits || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error loading visits")
    } finally {
      setLoading(false)
    }
  }

  const filteredVisits = visits.filter(visit => {
    const matchesSearch = 
      visit.patientName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      visit.patientMrn.toLowerCase().includes(searchTerm.toLowerCase()) ||
      visit.chiefComplaint.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesStatus = filterStatus === "all" || visit.status === filterStatus
    
    return matchesSearch && matchesStatus
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case "in-progress":
        return "bg-blue-950/50 text-blue-400 border-blue-800"
      case "completed":
        return "bg-green-950/50 text-green-400 border-green-800"
      case "pending":
        return "bg-yellow-950/50 text-yellow-400 border-yellow-800"
      default:
        return "bg-zinc-800 text-zinc-400 border-zinc-700"
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-400">Loading visits...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
              Patient Visits
            </h1>
            <p className="text-zinc-400">View and document patient encounters</p>
          </div>
          <Link
            href="/portals/carefusion/provider/visits/new"
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition"
          >
            New Visit
          </Link>
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
                placeholder="Search by patient name, MRN, or chief complaint..."
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
              <option value="pending">Pending</option>
              <option value="in-progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-zinc-950 border-b border-zinc-800">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Date & Time</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Patient</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Visit Type</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Chief Complaint</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Provider</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Status</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-zinc-300">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {filteredVisits.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-zinc-500">
                    No visits found
                  </td>
                </tr>
              ) : (
                filteredVisits.map((visit) => (
                  <tr key={visit.id} className="hover:bg-zinc-800/50 transition">
                    <td className="px-6 py-4">
                      <div className="font-medium">{visit.visitDate}</div>
                      <div className="text-sm text-zinc-400">{visit.visitTime}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium">{visit.patientName}</div>
                      <div className="text-xs text-zinc-500 font-mono">MRN: {visit.patientMrn}</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-zinc-400 capitalize">{visit.visitType}</td>
                    <td className="px-6 py-4 text-sm text-zinc-400">{visit.chiefComplaint}</td>
                    <td className="px-6 py-4 text-sm text-zinc-400">{visit.providerName}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(visit.status)}`}>
                        {visit.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        href={`/portals/carefusion/provider/visits/${visit.id}`}
                        className="text-purple-400 hover:text-purple-300 text-sm font-medium"
                      >
                        {visit.status === "completed" ? "View" : "Continue"}
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
