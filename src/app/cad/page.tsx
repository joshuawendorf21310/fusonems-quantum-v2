"use client";

import { useEffect, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import Link from "next/link";
import { PageShell } from "@/components/PageShell";

interface Incident {
  id: string;
  incident_number: string;
  incident_type: string;
  priority: string;
  status: string;
  address: string;
  created_at: string;
  assigned_units: string[];
  caller_info?: string;
}

interface UnitStatus {
  unit_id: string;
  status: string;
  current_incident?: string;
  last_updated: string;
}

export default function CADDashboard() {
  const [activeIncidents, setActiveIncidents] = useState<Incident[]>([]);
  const [unitStatuses, setUnitStatuses] = useState<UnitStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newIncidentOpen, setNewIncidentOpen] = useState(false);
  const [newIncidentSubmitting, setNewIncidentSubmitting] = useState(false);
  const [newIncidentError, setNewIncidentError] = useState<string | null>(null);
  const [newIncidentForm, setNewIncidentForm] = useState({
    requesting_facility: "",
    receiving_facility: "",
    transport_type: "IFT" as "IFT" | "NEMT" | "CCT",
    priority: "Routine",
    scheduled_time: "",
    notes: "",
  });

  const loadDashboardData = useCallback(async () => {
    try {
      const [incidents, units] = await Promise.all([
        apiFetch<Incident[]>("/api/cad/incidents/active").catch(() => []),
        apiFetch<UnitStatus[]>("/api/cad/units/status").catch(() => [])
      ]);
      setActiveIncidents(incidents);
      setUnitStatuses(units);
      setError(null);
    } catch (err) {
      setError("Failed to load CAD data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleCreateIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    setNewIncidentSubmitting(true);
    setNewIncidentError(null);

    try {
      await apiFetch("/api/cad/incidents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newIncidentForm),
      });
      
      setNewIncidentOpen(false);
      setNewIncidentForm({
        requesting_facility: "",
        receiving_facility: "",
        transport_type: "IFT",
        priority: "Routine",
        scheduled_time: "",
        notes: "",
      });
      
      loadDashboardData();
    } catch (err: any) {
      setNewIncidentError(err.message || "Failed to create incident");
    } finally {
      setNewIncidentSubmitting(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case "emergency": case "high": return "bg-red-600/20 text-red-400 border-red-600/30";
      case "urgent": case "medium": return "bg-orange-600/20 text-orange-400 border-orange-600/30";
      case "low": return "bg-blue-600/20 text-blue-400 border-blue-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "dispatched": return "bg-yellow-600/20 text-yellow-400 border-yellow-600/30";
      case "en_route": return "bg-blue-600/20 text-blue-400 border-blue-600/30";
      case "on_scene": return "bg-purple-600/20 text-purple-400 border-purple-600/30";
      case "transporting": return "bg-green-600/20 text-green-400 border-green-600/30";
      case "available": return "bg-green-600/20 text-green-400 border-green-600/30";
      case "unavailable": return "bg-red-600/20 text-red-400 border-red-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  return (
    <PageShell title="CAD System" requireAuth={true}>
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">CAD - Live Dispatch Board</h1>
            <p className="text-zinc-400 mt-1">Real-time incident and unit tracking</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/cad/units"
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
            >
              Units
            </Link>
            <Link
              href="/cad/incidents"
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
            >
              All Incidents
            </Link>
            <button
              type="button"
              onClick={() => setNewIncidentOpen(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-medium"
            >
              New Incident
            </button>
          </div>
        </div>

        {/* New Incident Modal */}
        {newIncidentOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => !newIncidentSubmitting && setNewIncidentOpen(false)}>
            <div className="bg-zinc-900 rounded-xl border border-zinc-700 shadow-xl max-w-md w-full p-6" onClick={(e) => e.stopPropagation()}>
              <h2 className="text-xl font-semibold mb-4">New CAD Incident</h2>
              {newIncidentError && (
                <div className="mb-4 p-3 rounded-lg bg-red-900/20 border border-red-600/30 text-red-400 text-sm">{newIncidentError}</div>
              )}
              <form onSubmit={handleCreateIncident} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1">Requesting Facility *</label>
                  <input
                    type="text"
                    required
                    value={newIncidentForm.requesting_facility}
                    onChange={(e) => setNewIncidentForm((f) => ({ ...f, requesting_facility: e.target.value }))}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="e.g. County General"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1">Receiving Facility *</label>
                  <input
                    type="text"
                    required
                    value={newIncidentForm.receiving_facility}
                    onChange={(e) => setNewIncidentForm((f) => ({ ...f, receiving_facility: e.target.value }))}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="e.g. Regional Medical Center"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1">Transport Type *</label>
                  <select
                    value={newIncidentForm.transport_type}
                    onChange={(e) => setNewIncidentForm((f) => ({ ...f, transport_type: e.target.value as "IFT" | "NEMT" | "CCT" }))}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="IFT">IFT</option>
                    <option value="NEMT">NEMT</option>
                    <option value="CCT">CCT</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1">Priority</label>
                  <select
                    value={newIncidentForm.priority}
                    onChange={(e) => setNewIncidentForm((f) => ({ ...f, priority: e.target.value }))}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="Routine">Routine</option>
                    <option value="Urgent">Urgent</option>
                    <option value="Emergency">Emergency</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1">Scheduled Time (optional)</label>
                  <input
                    type="datetime-local"
                    value={newIncidentForm.scheduled_time}
                    onChange={(e) => setNewIncidentForm((f) => ({ ...f, scheduled_time: e.target.value }))}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1">Notes (optional)</label>
                  <textarea
                    value={newIncidentForm.notes}
                    onChange={(e) => setNewIncidentForm((f) => ({ ...f, notes: e.target.value }))}
                    rows={2}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    placeholder="Additional notes..."
                  />
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setNewIncidentOpen(false)}
                    disabled={newIncidentSubmitting}
                    className="flex-1 px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg transition-colors disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={newIncidentSubmitting}
                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-medium disabled:opacity-50"
                  >
                    {newIncidentSubmitting ? "Creating..." : "Create Incident"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {loading && (
          <div className="text-center py-12 text-zinc-400">Loading dispatch board...</div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-600/30 text-red-400 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="grid grid-cols-3 gap-6">
            {/* Active Incidents */}
            <div className="col-span-2 space-y-4">
              <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold">Active Incidents</h2>
                  <span className="text-sm text-zinc-400">
                    {activeIncidents.length} active
                  </span>
                </div>

                {activeIncidents.length === 0 ? (
                  <div className="text-center py-8 text-zinc-400">
                    No active incidents
                  </div>
                ) : (
                  <div className="space-y-3">
                    {activeIncidents.map((incident) => (
                      <Link
                        key={incident.id}
                        href={`/cad/incidents/${incident.id}`}
                        className="block bg-zinc-800/50 hover:bg-zinc-800 rounded-lg p-4 transition-colors border border-zinc-700"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <div className="font-mono text-sm text-zinc-400">
                              {incident.incident_number}
                            </div>
                            <div className="font-semibold text-lg">
                              {incident.incident_type}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <span className={`px-2 py-1 rounded text-xs font-medium border ${getPriorityColor(incident.priority)}`}>
                              {incident.priority}
                            </span>
                            <span className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(incident.status)}`}>
                              {incident.status.replace("_", " ")}
                            </span>
                          </div>
                        </div>
                        <div className="text-sm text-zinc-400 mb-2">
                          {incident.address}
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="text-xs text-zinc-500">
                            {new Date(incident.created_at).toLocaleTimeString()}
                          </div>
                          {incident.assigned_units.length > 0 && (
                            <div className="flex gap-1">
                              {incident.assigned_units.map((unit) => (
                                <span
                                  key={unit}
                                  className="px-2 py-0.5 bg-blue-600/20 text-blue-400 rounded text-xs"
                                >
                                  {unit}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Unit Status */}
            <div className="col-span-1">
              <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6 sticky top-6">
                <h2 className="text-xl font-semibold mb-4">Unit Status</h2>
                {unitStatuses.length === 0 ? (
                  <div className="text-center py-8 text-zinc-400 text-sm">
                    No units available
                  </div>
                ) : (
                  <div className="space-y-2">
                    {unitStatuses.map((unit) => (
                      <div
                        key={unit.unit_id}
                        className="bg-zinc-800/50 rounded p-3 border border-zinc-700"
                      >
                        <div className="flex justify-between items-center mb-1">
                          <div className="font-semibold">{unit.unit_id}</div>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium border ${getStatusColor(unit.status)}`}>
                            {unit.status.replace("_", " ")}
                          </span>
                        </div>
                        {unit.current_incident && (
                          <div className="text-xs text-zinc-400 mt-1">
                            Incident: {unit.current_incident}
                          </div>
                        )}
                        <div className="text-xs text-zinc-500 mt-1">
                          Updated: {new Date(unit.last_updated).toLocaleTimeString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </PageShell>
  );
}
