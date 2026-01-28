"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import Link from "next/link";

interface IncidentDetail {
  id: string;
  incident_number: string;
  incident_type: string;
  priority: string;
  status: string;
  address: string;
  latitude?: number;
  longitude?: number;
  caller_name?: string;
  caller_phone?: string;
  chief_complaint?: string;
  notes?: string;
  created_at: string;
  closed_at?: string;
  assigned_units: string[];
}

interface TimelineEvent {
  id: string;
  event_type: string;
  description: string;
  timestamp: string;
  user?: string;
  unit?: string;
}

export default function IncidentDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    loadIncidentData();
  }, [id]);

  const loadIncidentData = async () => {
    setLoading(true);
    try {
      const [incidentData, timelineData] = await Promise.all([
        apiFetch<IncidentDetail>(`/api/cad/incidents/${id}`),
        apiFetch<TimelineEvent[]>(`/api/cad/incidents/${id}/timeline`).catch(() => [])
      ]);
      setIncident(incidentData);
      setTimeline(timelineData);
      setError(null);
    } catch (err) {
      setError("Failed to load incident details.");
    } finally {
      setLoading(false);
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
      case "closed": return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
        <div className="text-center py-12 text-zinc-400">Loading incident...</div>
      </div>
    );
  }

  if (error || !incident) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
        <div className="bg-red-900/20 border border-red-600/30 text-red-400 px-4 py-3 rounded-lg">
          {error || "Incident not found"}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Link href="/cad" className="text-zinc-400 hover:text-zinc-300">
                ← Back to Dispatch Board
              </Link>
            </div>
            <h1 className="text-3xl font-bold">Incident #{incident.incident_number}</h1>
            <p className="text-zinc-400 mt-1">{incident.incident_type}</p>
          </div>
          <div className="flex gap-3">
            <button className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors">
              Update Status
            </button>
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
              Assign Units
            </button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
            <div className="text-sm text-zinc-400 mb-1">Priority</div>
            <span className={`inline-block px-2 py-1 rounded text-xs font-medium border ${getPriorityColor(incident.priority)}`}>
              {incident.priority}
            </span>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
            <div className="text-sm text-zinc-400 mb-1">Status</div>
            <span className={`inline-block px-2 py-1 rounded text-xs font-medium border ${getStatusColor(incident.status)}`}>
              {incident.status.replace("_", " ")}
            </span>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
            <div className="text-sm text-zinc-400 mb-1">Created</div>
            <div className="font-semibold">{new Date(incident.created_at).toLocaleString()}</div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Incident Details */}
          <div className="col-span-2 space-y-6">
            <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
              <h2 className="text-xl font-semibold mb-4">Incident Details</h2>
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-zinc-400 mb-1">Location</div>
                  <div className="font-medium">{incident.address}</div>
                  {incident.latitude && incident.longitude && (
                    <div className="text-sm text-zinc-500 mt-1">
                      {incident.latitude.toFixed(6)}, {incident.longitude.toFixed(6)}
                    </div>
                  )}
                </div>
                {incident.caller_name && (
                  <div>
                    <div className="text-sm text-zinc-400 mb-1">Caller</div>
                    <div className="font-medium">{incident.caller_name}</div>
                    {incident.caller_phone && (
                      <div className="text-sm text-zinc-500">{incident.caller_phone}</div>
                    )}
                  </div>
                )}
                {incident.chief_complaint && (
                  <div>
                    <div className="text-sm text-zinc-400 mb-1">Chief Complaint</div>
                    <div className="font-medium">{incident.chief_complaint}</div>
                  </div>
                )}
                {incident.notes && (
                  <div>
                    <div className="text-sm text-zinc-400 mb-1">Notes</div>
                    <div className="text-zinc-300 whitespace-pre-wrap">{incident.notes}</div>
                  </div>
                )}
              </div>
            </div>

            {/* Timeline */}
            <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
              <h2 className="text-xl font-semibold mb-4">Incident Timeline</h2>
              {timeline.length === 0 ? (
                <div className="text-center py-8 text-zinc-400">No timeline events</div>
              ) : (
                <div className="space-y-3">
                  {timeline.map((event) => (
                    <div key={event.id} className="border-l-2 border-blue-600 pl-4 py-2">
                      <div className="flex justify-between items-start mb-1">
                        <div className="font-semibold">{event.description}</div>
                        <div className="text-xs text-zinc-400">
                          {new Date(event.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                      <div className="text-sm text-zinc-400">
                        {event.event_type}
                        {event.unit && ` • Unit: ${event.unit}`}
                        {event.user && ` • By: ${event.user}`}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Assigned Units */}
          <div className="col-span-1">
            <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6 sticky top-6">
              <h2 className="text-xl font-semibold mb-4">Assigned Units</h2>
              {incident.assigned_units.length === 0 ? (
                <div className="text-center py-8 text-zinc-400 text-sm">
                  No units assigned
                </div>
              ) : (
                <div className="space-y-2">
                  {incident.assigned_units.map((unit) => (
                    <div
                      key={unit}
                      className="bg-zinc-800/50 rounded p-3 border border-zinc-700"
                    >
                      <div className="font-semibold">{unit}</div>
                      <div className="text-xs text-zinc-400 mt-1">Active</div>
                    </div>
                  ))}
                </div>
              )}
              <button className="w-full mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors text-sm">
                Add Unit
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
