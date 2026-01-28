"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { 
  Plane, ArrowLeft, MapPin, Clock, Users, Activity, 
  Cloud, Save, AlertTriangle 
} from "lucide-react";

type MissionDetail = {
  id: number;
  mission_number: string;
  aircraft: string;
  tail_number: string;
  pilot: string;
  copilot: string | null;
  medical_crew: Array<{ name: string; role: string }>;
  departure_time: string;
  arrival_time: string | null;
  status: string;
  origin: string;
  destination: string;
  patient_name: string | null;
  patient_age: number | null;
  chief_complaint: string | null;
  flight_log: {
    departure_fuel: number;
    arrival_fuel: number | null;
    flight_hours: number | null;
    hobbs_start: number;
    hobbs_end: number | null;
    tach_start: number;
    tach_end: number | null;
    route: string;
    altitude: number;
    airspeed: number;
  };
  weather: {
    ceiling: number;
    visibility: number;
    wind_speed: number;
    wind_direction: number;
    temperature: number;
    conditions: string;
  };
  frat_score: number | null;
  notes: string;
};

export default function MissionDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const [mission, setMission] = useState<MissionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (id) {
      apiFetch<MissionDetail>(`/hems/missions/${id}`, { credentials: "include" })
        .then(setMission)
        .catch(() => setError("Failed to load mission details"))
        .finally(() => setLoading(false));
    }
  }, [id]);

  const handleSave = async () => {
    if (!mission) return;
    setSaving(true);
    try {
      await apiFetch(`/hems/missions/${id}`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(mission),
      });
      alert("Mission updated successfully");
    } catch (err) {
      alert("Failed to update mission");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="flex items-center gap-3 px-6 py-3 bg-zinc-900 rounded-full border border-zinc-800">
          <Plane className="w-5 h-5 text-sky-400 animate-pulse" />
          <span className="text-zinc-300">Loading mission...</span>
        </div>
      </div>
    );
  }

  if (error || !mission) {
    return (
      <div className="min-h-screen bg-zinc-950 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400">
            {error || "Mission not found"}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="bg-gradient-to-r from-sky-950 via-zinc-900 to-blue-950 border-b border-sky-900/30 px-6 py-6">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <Link href="/hems/missions" className="inline-flex items-center gap-2 text-zinc-400 hover:text-zinc-200 mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Missions
          </Link>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-sky-500 to-blue-500 rounded-xl">
                <Plane className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-zinc-100">{mission.mission_number}</h1>
                <p className="text-zinc-400">{mission.aircraft} ({mission.tail_number})</p>
              </div>
            </div>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 disabled:bg-zinc-700 text-white rounded-lg transition-colors"
            >
              <Save className="w-5 h-5" />
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </motion.div>
      </div>

      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Flight Overview */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-xl font-bold text-zinc-100 mb-4 flex items-center gap-2">
            <Activity className="w-6 h-6 text-sky-400" />
            Flight Overview
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-zinc-500">Departure Time</div>
              <div className="text-lg font-semibold text-zinc-100">{new Date(mission.departure_time).toLocaleString()}</div>
            </div>
            <div>
              <div className="text-sm text-zinc-500">Arrival Time</div>
              <div className="text-lg font-semibold text-zinc-100">
                {mission.arrival_time ? new Date(mission.arrival_time).toLocaleString() : 'In flight'}
              </div>
            </div>
            <div>
              <div className="text-sm text-zinc-500">Origin</div>
              <div className="text-lg font-semibold text-zinc-100">{mission.origin}</div>
            </div>
            <div>
              <div className="text-sm text-zinc-500">Destination</div>
              <div className="text-lg font-semibold text-zinc-100">{mission.destination}</div>
            </div>
          </div>
        </motion.div>

        {/* Crew */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-xl font-bold text-zinc-100 mb-4 flex items-center gap-2">
            <Users className="w-6 h-6 text-sky-400" />
            Flight Crew
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-zinc-800 rounded-lg p-4">
              <div className="text-sm text-zinc-500 mb-1">Pilot in Command</div>
              <div className="text-lg font-semibold text-zinc-100">{mission.pilot}</div>
            </div>
            {mission.copilot && (
              <div className="bg-zinc-800 rounded-lg p-4">
                <div className="text-sm text-zinc-500 mb-1">Co-Pilot</div>
                <div className="text-lg font-semibold text-zinc-100">{mission.copilot}</div>
              </div>
            )}
            <div className="bg-zinc-800 rounded-lg p-4">
              <div className="text-sm text-zinc-500 mb-1">Medical Crew</div>
              <div className="space-y-1">
                {mission.medical_crew.map((crew, idx) => (
                  <div key={idx} className="text-sm text-zinc-100">{crew.name} ({crew.role})</div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Flight Log */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-xl font-bold text-zinc-100 mb-4 flex items-center gap-2">
            <Plane className="w-6 h-6 text-sky-400" />
            Flight Log
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-zinc-500">Route</div>
              <div className="text-zinc-100 font-semibold">{mission.flight_log.route}</div>
            </div>
            <div>
              <div className="text-sm text-zinc-500">Altitude</div>
              <div className="text-zinc-100 font-semibold">{mission.flight_log.altitude} ft</div>
            </div>
            <div>
              <div className="text-sm text-zinc-500">Airspeed</div>
              <div className="text-zinc-100 font-semibold">{mission.flight_log.airspeed} kts</div>
            </div>
            <div>
              <div className="text-sm text-zinc-500">Flight Hours</div>
              <div className="text-zinc-100 font-semibold">
                {mission.flight_log.flight_hours ? mission.flight_log.flight_hours.toFixed(2) : 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-sm text-zinc-500">Hobbs Start</div>
              <div className="text-zinc-100">{mission.flight_log.hobbs_start}</div>
            </div>
            <div>
              <div className="text-sm text-zinc-500">Hobbs End</div>
              <div className="text-zinc-100">{mission.flight_log.hobbs_end || 'N/A'}</div>
            </div>
            <div>
              <div className="text-sm text-zinc-500">Departure Fuel</div>
              <div className="text-zinc-100">{mission.flight_log.departure_fuel} gal</div>
            </div>
            <div>
              <div className="text-sm text-zinc-500">Arrival Fuel</div>
              <div className="text-zinc-100">{mission.flight_log.arrival_fuel || 'N/A'} gal</div>
            </div>
          </div>
        </motion.div>

        {/* Weather */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-xl font-bold text-zinc-100 mb-4 flex items-center gap-2">
            <Cloud className="w-6 h-6 text-sky-400" />
            Weather Conditions
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-zinc-800 rounded-lg p-4">
              <div className="text-sm text-zinc-500 mb-1">Conditions</div>
              <div className="text-lg font-semibold text-zinc-100">{mission.weather.conditions}</div>
            </div>
            <div className="bg-zinc-800 rounded-lg p-4">
              <div className="text-sm text-zinc-500 mb-1">Ceiling</div>
              <div className="text-lg font-semibold text-zinc-100">{mission.weather.ceiling} ft</div>
            </div>
            <div className="bg-zinc-800 rounded-lg p-4">
              <div className="text-sm text-zinc-500 mb-1">Visibility</div>
              <div className="text-lg font-semibold text-zinc-100">{mission.weather.visibility} mi</div>
            </div>
            <div className="bg-zinc-800 rounded-lg p-4">
              <div className="text-sm text-zinc-500 mb-1">Wind</div>
              <div className="text-lg font-semibold text-zinc-100">
                {mission.weather.wind_direction}° @ {mission.weather.wind_speed} kts
              </div>
            </div>
            <div className="bg-zinc-800 rounded-lg p-4">
              <div className="text-sm text-zinc-500 mb-1">Temperature</div>
              <div className="text-lg font-semibold text-zinc-100">{mission.weather.temperature}°F</div>
            </div>
          </div>
        </motion.div>

        {/* Patient Info */}
        {mission.patient_name && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-bold text-zinc-100 mb-4">Patient Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-zinc-500">Patient Name</div>
                <div className="text-lg font-semibold text-zinc-100">{mission.patient_name}</div>
              </div>
              <div>
                <div className="text-sm text-zinc-500">Age</div>
                <div className="text-lg font-semibold text-zinc-100">{mission.patient_age || 'N/A'}</div>
              </div>
              <div>
                <div className="text-sm text-zinc-500">Chief Complaint</div>
                <div className="text-lg font-semibold text-zinc-100">{mission.chief_complaint || 'N/A'}</div>
              </div>
            </div>
          </motion.div>
        )}

        {/* FRAT Score */}
        {mission.frat_score !== null && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} 
            className={`border rounded-xl p-6 ${
              mission.frat_score < 20 ? 'bg-green-500/10 border-green-500/30' :
              mission.frat_score < 40 ? 'bg-amber-500/10 border-amber-500/30' :
              'bg-red-500/10 border-red-500/30'
            }`}
          >
            <div className="flex items-center gap-3">
              <AlertTriangle className={`w-6 h-6 ${
                mission.frat_score < 20 ? 'text-green-400' :
                mission.frat_score < 40 ? 'text-amber-400' :
                'text-red-400'
              }`} />
              <div>
                <h3 className="text-lg font-bold text-zinc-100">Flight Risk Assessment</h3>
                <div className="text-2xl font-bold mt-1">
                  FRAT Score: <span className={
                    mission.frat_score < 20 ? 'text-green-400' :
                    mission.frat_score < 40 ? 'text-amber-400' :
                    'text-red-400'
                  }>{mission.frat_score}</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Notes */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-xl font-bold text-zinc-100 mb-4">Mission Notes</h2>
          <textarea
            value={mission.notes}
            onChange={(e) => setMission({ ...mission, notes: e.target.value })}
            className="w-full h-32 bg-zinc-800 border border-zinc-700 rounded-lg p-4 text-zinc-100 focus:outline-none focus:border-sky-500"
            placeholder="Enter mission notes..."
          />
        </motion.div>
      </div>
    </div>
  );
}
