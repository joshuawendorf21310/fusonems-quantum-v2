"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import Link from "next/link";
import { NemsisRecordActions } from "@/components/epcr";

interface PCRData {
  id: string;
  incident_number: string;
  unit: string;
  patient_name: string;
  patient_dob: string;
  patient_gender: string;
  chief_complaint: string;
  status: string;
  created_at: string;
  updated_at: string;
  vitals?: {
    bp_systolic?: number;
    bp_diastolic?: number;
    heart_rate?: number;
    respiratory_rate?: number;
    oxygen_saturation?: number;
    temperature?: number;
    glucose?: number;
  };
  assessment?: {
    level_of_consciousness?: string;
    findings?: string;
  };
  interventions?: string;
  medications?: string;
  narrative?: string;
  disposition?: string;
  destination_facility?: string;
}

export default function EPCRDetail() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;
  const [pcr, setPcr] = useState<PCRData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!id) return;
    loadPCR();
  }, [id]);

  const loadPCR = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<PCRData>(`/api/epcr/pcrs/${id}`);
      setPcr(data);
      setError(null);
    } catch (err) {
      setError("Failed to load PCR details.");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!pcr) return;
    setSaving(true);
    try {
      await apiFetch(`/api/epcr/pcrs/${id}`, {
        method: "PUT",
        body: JSON.stringify(pcr)
      });
      setEditMode(false);
      loadPCR();
    } catch (err) {
      setError("Failed to save changes.");
    } finally {
      setSaving(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed": return "bg-green-600/20 text-green-400 border-green-600/30";
      case "in_progress": return "bg-yellow-600/20 text-yellow-400 border-yellow-600/30";
      case "pending": return "bg-blue-600/20 text-blue-400 border-blue-600/30";
      case "review": return "bg-purple-600/20 text-purple-400 border-purple-600/30";
      default: return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
        <div className="text-center py-12 text-zinc-400">Loading PCR...</div>
      </div>
    );
  }

  if (error || !pcr) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
        <div className="bg-red-900/20 border border-red-600/30 text-red-400 px-4 py-3 rounded-lg">
          {error || "PCR not found"}
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
              <Link href="/epcr" className="text-zinc-400 hover:text-zinc-300">
                ← Back to ePCR
              </Link>
            </div>
            <h1 className="text-3xl font-bold">PCR #{pcr.incident_number}</h1>
            <p className="text-zinc-400 mt-1">{pcr.patient_name}</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <NemsisRecordActions recordId={id} stateCode="WI" compact />
            {editMode ? (
              <>
                <button
                  onClick={() => setEditMode(false)}
                  className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-medium disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save Changes"}
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setEditMode(true)}
                  className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
                >
                  Edit PCR
                </button>
                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors">
                  Export PDF
                </button>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
            <div className="text-sm text-zinc-400 mb-1">Status</div>
            <span className={`inline-block px-2 py-1 rounded text-xs font-medium border ${getStatusColor(pcr.status)}`}>
              {pcr.status}
            </span>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
            <div className="text-sm text-zinc-400 mb-1">Unit</div>
            <div className="font-semibold">{pcr.unit}</div>
          </div>
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
            <div className="text-sm text-zinc-400 mb-1">Created</div>
            <div className="font-semibold">{new Date(pcr.created_at).toLocaleString()}</div>
          </div>
        </div>

        <div className="space-y-6">
          {/* Patient Information */}
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <h2 className="text-xl font-semibold mb-4">Patient Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-zinc-400 mb-1">Name</div>
                <div className="font-medium">{pcr.patient_name}</div>
              </div>
              <div>
                <div className="text-sm text-zinc-400 mb-1">Date of Birth</div>
                <div className="font-medium">{pcr.patient_dob}</div>
              </div>
              <div>
                <div className="text-sm text-zinc-400 mb-1">Gender</div>
                <div className="font-medium capitalize">{pcr.patient_gender}</div>
              </div>
              <div>
                <div className="text-sm text-zinc-400 mb-1">Chief Complaint</div>
                <div className="font-medium">{pcr.chief_complaint}</div>
              </div>
            </div>
          </div>

          {/* Vital Signs */}
          {pcr.vitals && (
            <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
              <h2 className="text-xl font-semibold mb-4">Vital Signs</h2>
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-zinc-400 mb-1">Blood Pressure</div>
                  <div className="font-medium">
                    {pcr.vitals.bp_systolic}/{pcr.vitals.bp_diastolic} mmHg
                  </div>
                </div>
                <div>
                  <div className="text-sm text-zinc-400 mb-1">Heart Rate</div>
                  <div className="font-medium">{pcr.vitals.heart_rate} bpm</div>
                </div>
                <div>
                  <div className="text-sm text-zinc-400 mb-1">Respiratory Rate</div>
                  <div className="font-medium">{pcr.vitals.respiratory_rate} /min</div>
                </div>
                <div>
                  <div className="text-sm text-zinc-400 mb-1">O2 Saturation</div>
                  <div className="font-medium">{pcr.vitals.oxygen_saturation}%</div>
                </div>
              </div>
            </div>
          )}

          {/* Assessment */}
          {pcr.assessment && (
            <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
              <h2 className="text-xl font-semibold mb-4">Assessment</h2>
              <div className="space-y-3">
                <div>
                  <div className="text-sm text-zinc-400 mb-1">Level of Consciousness</div>
                  <div className="font-medium capitalize">{pcr.assessment.level_of_consciousness}</div>
                </div>
                <div>
                  <div className="text-sm text-zinc-400 mb-1">Findings</div>
                  <div className="text-zinc-300">{pcr.assessment.findings || "None documented"}</div>
                </div>
              </div>
            </div>
          )}

          {/* Interventions */}
          {pcr.interventions && (
            <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
              <h2 className="text-xl font-semibold mb-4">Interventions</h2>
              <div className="text-zinc-300 whitespace-pre-wrap">{pcr.interventions}</div>
            </div>
          )}

          {/* Medications */}
          {pcr.medications && (
            <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
              <h2 className="text-xl font-semibold mb-4">Medications</h2>
              <div className="text-zinc-300 whitespace-pre-wrap">{pcr.medications}</div>
            </div>
          )}

          {/* Narrative */}
          {pcr.narrative && (
            <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
              <h2 className="text-xl font-semibold mb-4">Narrative</h2>
              <div className="text-zinc-300 whitespace-pre-wrap">{pcr.narrative}</div>
            </div>
          )}

          {/* Disposition */}
          <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
            <h2 className="text-xl font-semibold mb-4">Disposition</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-zinc-400 mb-1">Disposition</div>
                <div className="font-medium capitalize">{pcr.disposition}</div>
              </div>
              <div>
                <div className="text-sm text-zinc-400 mb-1">Destination Facility</div>
                <div className="font-medium">{pcr.destination_facility || "N/A"}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
