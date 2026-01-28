"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import Link from "next/link";

interface Unit {
  unit_id: string;
  unit_type: string;
  status: string;
  current_incident?: string;
  current_incident_id?: string;
  personnel?: string[];
  last_updated: string;
  location?: string;
}

export default function UnitsPage() {
  const [units, setUnits] = useState<Unit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    loadUnits();
    const interval = setInterval(loadUnits, 15000); // Refresh every 15s
    return () => clearInterval(interval);
  }, [statusFilter]);

  const loadUnits = async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.append("status", statusFilter);

      const data = await apiFetch<Unit[]>(`/api/cad/units?${params.toString()}`);
      setUnits(data);
      setError(null);
    } catch (err) {
      setError("Failed to load unit data.");
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "available": return "bg-green-600/20 text-green-400 border-green-600/30";
      case "dispatched": return "bg-yellow-600/20 text-yellow-400 border-yellow-600/30";
      case "en_route": return "bg-blue-600/20 text-blue-400 border-blue-600/30";
      case "on_scene": return "bg-purple-600/20 text-purple-400 border-purple-600/30";
      case "transporting": return "bg-cyan-600/20 text-cyan-400 border-cyan-600/30";
      case "unavailable": case "out_of_service": return "bg-red-600/20 text-red-400 border-red-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  const availableUnits = units.filter(u => u.status === "available").length;
  const busyUnits = units.filter(u => ["dispatched", "en_route", "on_scene", "transporting"].includes(u.status)).length;
  const unavailableUnits = units.filter(u => ["unavailable", "out_of_service"].includes(u.status)).length;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Unit Status Board</h1>
            <p className="text-zinc-400 mt-1">Real-time unit tracking and availability</p>
          </div>
          <Link
            href="/cad"
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
          >
            ← Back to Dispatch Board
          </Link>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-600/30 text-red-400 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-blue-400">{units.length}</div>
            <div className="text-sm text-zinc-400 mt-1">Total Units</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-green-400">{availableUnits}</div>
            <div className="text-sm text-zinc-400 mt-1">Available</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-yellow-400">{busyUnits}</div>
            <div className="text-sm text-zinc-400 mt-1">Busy</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <div className="text-3xl font-bold text-red-400">{unavailableUnits}</div>
            <div className="text-sm text-zinc-400 mt-1">Unavailable</div>
          </div>
        </div>

        {/* Filter */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4 mb-6">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-zinc-800 border border-zinc-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Status</option>
            <option value="available">Available</option>
            <option value="dispatched">Dispatched</option>
            <option value="en_route">En Route</option>
            <option value="on_scene">On Scene</option>
            <option value="transporting">Transporting</option>
            <option value="unavailable">Unavailable</option>
          </select>
        </div>

        {/* Units Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {loading ? (
            <div className="col-span-full text-center py-12 text-zinc-400">Loading units...</div>
          ) : units.length === 0 ? (
            <div className="col-span-full text-center py-12 text-zinc-400">
              No units found.
            </div>
          ) : (
            units.map((unit) => (
              <div
                key={unit.unit_id}
                className="bg-zinc-900 rounded-lg border border-zinc-800 p-6 hover:border-zinc-700 transition-colors"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-bold">{unit.unit_id}</h3>
                    <div className="text-sm text-zinc-400">{unit.unit_type}</div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(unit.status)}`}>
                    {unit.status.replace("_", " ")}
                  </span>
                </div>

                {unit.location && (
                  <div className="mb-3">
                    <div className="text-xs text-zinc-500 mb-1">Location</div>
                    <div className="text-sm text-zinc-300">{unit.location}</div>
                  </div>
                )}

                {unit.current_incident && (
                  <div className="mb-3">
                    <div className="text-xs text-zinc-500 mb-1">Current Incident</div>
                    {unit.current_incident_id ? (
                      <Link
                        href={`/cad/incidents/${unit.current_incident_id}`}
                        className="text-sm text-blue-400 hover:text-blue-300"
                      >
                        {unit.current_incident}
                      </Link>
                    ) : (
                      <div className="text-sm text-zinc-300">{unit.current_incident}</div>
                    )}
                  </div>
                )}

                {unit.personnel && unit.personnel.length > 0 && (
                  <div className="mb-3">
                    <div className="text-xs text-zinc-500 mb-1">Personnel</div>
                    <div className="flex flex-wrap gap-1">
                      {unit.personnel.map((person, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-zinc-800 rounded text-xs"
                        >
                          {person}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="text-xs text-zinc-500 mt-4">
                  Updated: {new Date(unit.last_updated).toLocaleTimeString()}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
