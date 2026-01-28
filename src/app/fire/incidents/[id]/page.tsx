"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { 
  AlertTriangle, ArrowLeft, MapPin, Clock, Flame, Users, 
  DollarSign, FileText, Truck, ThermometerSun, Save 
} from "lucide-react";

type FireIncidentDetail = {
  id: number;
  incident_number: string;
  incident_type: string;
  nfirs: {
    incident_type: string;
    incident_date: string;
    alarm_time: string;
    arrival_time: string;
    controlled_time: string | null;
    last_unit_cleared: string | null;
    actions_taken: string[];
    property_use: string;
    on_scene_units: number;
    casualties: {
      civilian_deaths: number;
      civilian_injuries: number;
      fire_deaths: number;
      fire_injuries: number;
    };
    property_loss: number;
    contents_loss: number;
    fire_spread: string;
    ignition_source: string;
    heat_source: string;
    item_ignited: string;
    area_of_origin: string;
    structure_type: string;
    structure_status: string;
    fire_suppression_factors: string[];
    detector_presence: boolean;
    detector_operated: boolean | null;
    sprinkler_presence: boolean;
    sprinkler_operated: boolean | null;
  };
  address: string;
  latitude: number | null;
  longitude: number | null;
  status: string;
  narrative: string;
  units: Array<{
    unit_id: string;
    unit_name: string;
    dispatched: string;
    arrived: string;
    cleared: string;
  }>;
  personnel: Array<{
    name: string;
    role: string;
    unit: string;
  }>;
};

export default function FireIncidentDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const [incident, setIncident] = useState<FireIncidentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (id) {
      apiFetch<FireIncidentDetail>(`/fire/incidents/${id}`, { credentials: "include" })
        .then(setIncident)
        .catch(() => setError("Failed to load incident details"))
        .finally(() => setLoading(false));
    }
  }, [id]);

  const handleSave = async () => {
    if (!incident) return;
    setSaving(true);
    try {
      await apiFetch(`/fire/incidents/${id}`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(incident),
      });
      alert("Incident updated successfully");
    } catch (err) {
      alert("Failed to update incident");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="flex items-center gap-3 px-6 py-3 bg-zinc-900 rounded-full border border-zinc-800">
          <Flame className="w-5 h-5 text-red-400 animate-pulse" />
          <span className="text-zinc-300">Loading incident...</span>
        </div>
      </div>
    );
  }

  if (error || !incident) {
    return (
      <div className="min-h-screen bg-zinc-950 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400">
            {error || "Incident not found"}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-950 via-zinc-900 to-orange-950 border-b border-red-900/30 px-6 py-6">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Link
            href="/fire/incidents"
            className="inline-flex items-center gap-2 text-zinc-400 hover:text-zinc-200 mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Incidents
          </Link>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-red-500 to-orange-500 rounded-xl">
                <Flame className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-zinc-100">{incident.incident_number}</h1>
                <p className="text-zinc-400">{incident.incident_type} - NFIRS {incident.nfirs.incident_type}</p>
              </div>
            </div>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-zinc-700 text-white rounded-lg transition-colors"
            >
              <Save className="w-5 h-5" />
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </motion.div>
      </div>

      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Basic Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-6"
        >
          <h2 className="text-xl font-bold text-zinc-100 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-red-400" />
            Incident Overview
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-2 text-zinc-400">
              <MapPin className="w-4 h-4" />
              <span className="font-medium text-zinc-300">{incident.address}</span>
            </div>
            <div className="flex items-center gap-2 text-zinc-400">
              <Clock className="w-4 h-4" />
              Alarm: {new Date(incident.nfirs.alarm_time).toLocaleString()}
            </div>
            <div className="flex items-center gap-2 text-zinc-400">
              <Clock className="w-4 h-4" />
              Arrival: {new Date(incident.nfirs.arrival_time).toLocaleString()}
            </div>
            {incident.nfirs.controlled_time && (
              <div className="flex items-center gap-2 text-zinc-400">
                <Clock className="w-4 h-4" />
                Controlled: {new Date(incident.nfirs.controlled_time).toLocaleString()}
              </div>
            )}
          </div>
        </motion.div>

        {/* NFIRS Data */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-6"
        >
          <h2 className="text-xl font-bold text-zinc-100 mb-4 flex items-center gap-2">
            <FileText className="w-6 h-6 text-orange-400" />
            NFIRS Incident Data
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Fire Details */}
            <div className="space-y-3">
              <h3 className="font-semibold text-zinc-200 border-b border-zinc-700 pb-2">Fire Details</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-zinc-400">Property Use:</span>
                  <div className="text-zinc-100">{incident.nfirs.property_use}</div>
                </div>
                <div>
                  <span className="text-zinc-400">Structure Type:</span>
                  <div className="text-zinc-100">{incident.nfirs.structure_type}</div>
                </div>
                <div>
                  <span className="text-zinc-400">Fire Spread:</span>
                  <div className="text-zinc-100">{incident.nfirs.fire_spread}</div>
                </div>
              </div>
            </div>

            {/* Ignition */}
            <div className="space-y-3">
              <h3 className="font-semibold text-zinc-200 border-b border-zinc-700 pb-2">Ignition & Origin</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-zinc-400">Ignition Source:</span>
                  <div className="text-zinc-100">{incident.nfirs.ignition_source}</div>
                </div>
                <div>
                  <span className="text-zinc-400">Heat Source:</span>
                  <div className="text-zinc-100">{incident.nfirs.heat_source}</div>
                </div>
                <div>
                  <span className="text-zinc-400">Item Ignited:</span>
                  <div className="text-zinc-100">{incident.nfirs.item_ignited}</div>
                </div>
                <div>
                  <span className="text-zinc-400">Area of Origin:</span>
                  <div className="text-zinc-100">{incident.nfirs.area_of_origin}</div>
                </div>
              </div>
            </div>

            {/* Protection Systems */}
            <div className="space-y-3">
              <h3 className="font-semibold text-zinc-200 border-b border-zinc-700 pb-2">Protection Systems</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-zinc-400">Smoke Detector:</span>
                  <div className="text-zinc-100">
                    {incident.nfirs.detector_presence ? 
                      (incident.nfirs.detector_operated ? "Present & Operated" : "Present - Did Not Operate") 
                      : "Not Present"}
                  </div>
                </div>
                <div>
                  <span className="text-zinc-400">Sprinkler System:</span>
                  <div className="text-zinc-100">
                    {incident.nfirs.sprinkler_presence ? 
                      (incident.nfirs.sprinkler_operated ? "Present & Operated" : "Present - Did Not Operate") 
                      : "Not Present"}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Casualties & Losses */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          {/* Casualties */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-bold text-zinc-100 mb-4 flex items-center gap-2">
              <Users className="w-6 h-6 text-red-400" />
              Casualties
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-red-400">{incident.nfirs.casualties.civilian_deaths}</div>
                <div className="text-sm text-zinc-400 mt-1">Civilian Deaths</div>
              </div>
              <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-orange-400">{incident.nfirs.casualties.civilian_injuries}</div>
                <div className="text-sm text-zinc-400 mt-1">Civilian Injuries</div>
              </div>
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-red-400">{incident.nfirs.casualties.fire_deaths}</div>
                <div className="text-sm text-zinc-400 mt-1">Firefighter Deaths</div>
              </div>
              <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-orange-400">{incident.nfirs.casualties.fire_injuries}</div>
                <div className="text-sm text-zinc-400 mt-1">Firefighter Injuries</div>
              </div>
            </div>
          </div>

          {/* Property Loss */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h2 className="text-xl font-bold text-zinc-100 mb-4 flex items-center gap-2">
              <DollarSign className="w-6 h-6 text-amber-400" />
              Property Loss
            </h2>
            <div className="space-y-4">
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
                <div className="text-sm text-zinc-400 mb-1">Property Loss</div>
                <div className="text-3xl font-bold text-amber-400">
                  ${incident.nfirs.property_loss.toLocaleString()}
                </div>
              </div>
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
                <div className="text-sm text-zinc-400 mb-1">Contents Loss</div>
                <div className="text-3xl font-bold text-amber-400">
                  ${incident.nfirs.contents_loss.toLocaleString()}
                </div>
              </div>
              <div className="bg-zinc-800 rounded-lg p-4">
                <div className="text-sm text-zinc-400 mb-1">Total Loss</div>
                <div className="text-2xl font-bold text-zinc-100">
                  ${(incident.nfirs.property_loss + incident.nfirs.contents_loss).toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Units Responded */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-6"
        >
          <h2 className="text-xl font-bold text-zinc-100 mb-4 flex items-center gap-2">
            <Truck className="w-6 h-6 text-orange-400" />
            Units Responded ({incident.units.length})
          </h2>
          <div className="space-y-2">
            {incident.units.map((unit, idx) => (
              <div key={idx} className="bg-zinc-800 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="font-semibold text-zinc-100">{unit.unit_name}</div>
                  <div className="text-sm text-zinc-400">ID: {unit.unit_id}</div>
                </div>
                <div className="grid grid-cols-3 gap-4 mt-2 text-sm text-zinc-400">
                  <div>Dispatched: {new Date(unit.dispatched).toLocaleTimeString()}</div>
                  <div>Arrived: {new Date(unit.arrived).toLocaleTimeString()}</div>
                  <div>Cleared: {new Date(unit.cleared).toLocaleTimeString()}</div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Narrative */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-6"
        >
          <h2 className="text-xl font-bold text-zinc-100 mb-4">Incident Narrative</h2>
          <textarea
            value={incident.narrative}
            onChange={(e) => setIncident({ ...incident, narrative: e.target.value })}
            className="w-full h-48 bg-zinc-800 border border-zinc-700 rounded-lg p-4 text-zinc-100 focus:outline-none focus:border-red-500"
            placeholder="Enter incident narrative..."
          />
        </motion.div>
      </div>
    </div>
  );
}
