"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { TerminologySuggest, NarrativeWithDictation } from "@/components/epcr";

interface FormData {
  incident_number: string;
  unit: string;
  response_date: string;
  response_time: string;
  // Patient Demographics
  patient_first_name: string;
  patient_last_name: string;
  patient_dob: string;
  patient_gender: string;
  patient_age: string;
  // Chief Complaint
  chief_complaint: string;
  chief_complaint_code: string;
  complaint_onset: string;
  // Vitals
  bp_systolic: string;
  bp_diastolic: string;
  heart_rate: string;
  respiratory_rate: string;
  oxygen_saturation: string;
  temperature: string;
  glucose: string;
  // Assessment
  level_of_consciousness: string;
  assessment_findings: string;
  // Interventions
  interventions: string;
  // Medications
  medications: string;
  // Narrative
  narrative: string;
  // Disposition
  disposition: string;
  destination_facility: string;
}

export default function NewPCRPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState("incident");
  
  const [formData, setFormData] = useState<FormData>({
    incident_number: "",
    unit: "",
    response_date: new Date().toISOString().split('T')[0],
    response_time: new Date().toTimeString().slice(0, 5),
    patient_first_name: "",
    patient_last_name: "",
    patient_dob: "",
    patient_gender: "",
    patient_age: "",
    chief_complaint: "",
    chief_complaint_code: "",
    complaint_onset: "",
    bp_systolic: "",
    bp_diastolic: "",
    heart_rate: "",
    respiratory_rate: "",
    oxygen_saturation: "",
    temperature: "",
    glucose: "",
    level_of_consciousness: "",
    assessment_findings: "",
    interventions: "",
    medications: "",
    narrative: "",
    disposition: "",
    destination_facility: ""
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await apiFetch<{ id: number; record_id: number; patient_id: number; incident_number: string }>("/api/epcr/pcrs", {
        method: "POST",
        body: JSON.stringify({
          incident_number: formData.incident_number,
          unit: formData.unit,
          response_date: formData.response_date,
          response_time: formData.response_time,
          patient_first_name: formData.patient_first_name,
          patient_last_name: formData.patient_last_name,
          patient_dob: formData.patient_dob,
          patient_gender: formData.patient_gender,
          patient_age: formData.patient_age,
          chief_complaint: formData.chief_complaint,
          chief_complaint_code: formData.chief_complaint_code || undefined,
          complaint_onset: formData.complaint_onset,
          bp_systolic: formData.bp_systolic,
          bp_diastolic: formData.bp_diastolic,
          heart_rate: formData.heart_rate,
          respiratory_rate: formData.respiratory_rate,
          oxygen_saturation: formData.oxygen_saturation,
          temperature: formData.temperature,
          glucose: formData.glucose,
          level_of_consciousness: formData.level_of_consciousness,
          assessment_findings: formData.assessment_findings,
          interventions: formData.interventions,
          medications: formData.medications,
          narrative: formData.narrative,
          disposition: formData.disposition,
          destination_facility: formData.destination_facility,
        })
      });
      router.push(`/epcr/${response.record_id}`);
    } catch (err) {
      setError("Failed to create PCR. Please try again.");
      setLoading(false);
    }
  };

  const sections = [
    { id: "incident", label: "Incident Info" },
    { id: "patient", label: "Patient Demographics" },
    { id: "complaint", label: "Chief Complaint" },
    { id: "vitals", label: "Vitals" },
    { id: "assessment", label: "Assessment" },
    { id: "interventions", label: "Interventions" },
    { id: "medications", label: "Medications" },
    { id: "narrative", label: "Narrative" },
    { id: "disposition", label: "Disposition" }
  ];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-7xl mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">New Patient Care Report</h1>
          <p className="text-zinc-400 mt-1">Complete all required sections</p>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-600/30 text-red-400 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <div className="grid grid-cols-12 gap-6">
          {/* Section Navigation */}
          <div className="col-span-3">
            <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4 sticky top-6">
              <h3 className="font-semibold mb-3 text-sm uppercase text-zinc-400">Sections</h3>
              <nav className="space-y-1">
                {sections.map(section => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                      activeSection === section.id
                        ? "bg-blue-600 text-white"
                        : "hover:bg-zinc-800 text-zinc-300"
                    }`}
                  >
                    {section.label}
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Form Content */}
          <div className="col-span-9">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Incident Info */}
              {activeSection === "incident" && (
                <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
                  <h2 className="text-xl font-semibold mb-4">Incident Information</h2>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Incident Number *</label>
                      <input
                        type="text"
                        name="incident_number"
                        value={formData.incident_number}
                        onChange={handleChange}
                        required
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Unit *</label>
                      <input
                        type="text"
                        name="unit"
                        value={formData.unit}
                        onChange={handleChange}
                        required
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Response Date *</label>
                      <input
                        type="date"
                        name="response_date"
                        value={formData.response_date}
                        onChange={handleChange}
                        required
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Response Time *</label>
                      <input
                        type="time"
                        name="response_time"
                        value={formData.response_time}
                        onChange={handleChange}
                        required
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Patient Demographics */}
              {activeSection === "patient" && (
                <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
                  <h2 className="text-xl font-semibold mb-4">Patient Demographics</h2>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">First Name *</label>
                      <input
                        type="text"
                        name="patient_first_name"
                        value={formData.patient_first_name}
                        onChange={handleChange}
                        required
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Last Name *</label>
                      <input
                        type="text"
                        name="patient_last_name"
                        value={formData.patient_last_name}
                        onChange={handleChange}
                        required
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Date of Birth *</label>
                      <input
                        type="date"
                        name="patient_dob"
                        value={formData.patient_dob}
                        onChange={handleChange}
                        required
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Age</label>
                      <input
                        type="number"
                        name="patient_age"
                        value={formData.patient_age}
                        onChange={handleChange}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Gender *</label>
                      <select
                        name="patient_gender"
                        value={formData.patient_gender}
                        onChange={handleChange}
                        required
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                      >
                        <option value="">Select...</option>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                        <option value="other">Other</option>
                        <option value="unknown">Unknown</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* Chief Complaint */}
              {activeSection === "complaint" && (
                <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
                  <h2 className="text-xl font-semibold mb-4">Chief Complaint</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Chief Complaint *</label>
                      <input
                        type="text"
                        name="chief_complaint"
                        value={formData.chief_complaint}
                        onChange={handleChange}
                        required
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                        placeholder="e.g., Chest pain, Difficulty breathing"
                      />
                    </div>
                    <div>
                      <TerminologySuggest
                        query={formData.chief_complaint}
                        codeSet="icd10"
                        label="Suggest ICD-10 codes from chief complaint"
                        onSelect={(code, description) =>
                          setFormData((prev) => ({
                            ...prev,
                            chief_complaint_code: code,
                          }))
                        }
                        selectedCode={formData.chief_complaint_code}
                        selectedDescription={
                          formData.chief_complaint_code
                            ? undefined
                            : undefined
                        }
                      />
                      {formData.chief_complaint_code && (
                        <div className="text-sm text-zinc-400 mt-1">
                          Selected code: <span className="font-mono text-orange-400">{formData.chief_complaint_code}</span>
                        </div>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Onset</label>
                      <input
                        type="text"
                        name="complaint_onset"
                        value={formData.complaint_onset}
                        onChange={handleChange}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                        placeholder="e.g., 2 hours ago, Sudden"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Vitals */}
              {activeSection === "vitals" && (
                <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
                  <h2 className="text-xl font-semibold mb-4">Vital Signs</h2>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">BP Systolic</label>
                      <input
                        type="number"
                        name="bp_systolic"
                        value={formData.bp_systolic}
                        onChange={handleChange}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                        placeholder="mmHg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">BP Diastolic</label>
                      <input
                        type="number"
                        name="bp_diastolic"
                        value={formData.bp_diastolic}
                        onChange={handleChange}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                        placeholder="mmHg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Heart Rate</label>
                      <input
                        type="number"
                        name="heart_rate"
                        value={formData.heart_rate}
                        onChange={handleChange}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                        placeholder="bpm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Respiratory Rate</label>
                      <input
                        type="number"
                        name="respiratory_rate"
                        value={formData.respiratory_rate}
                        onChange={handleChange}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                        placeholder="breaths/min"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">O2 Saturation</label>
                      <input
                        type="number"
                        name="oxygen_saturation"
                        value={formData.oxygen_saturation}
                        onChange={handleChange}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                        placeholder="%"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Temperature</label>
                      <input
                        type="number"
                        step="0.1"
                        name="temperature"
                        value={formData.temperature}
                        onChange={handleChange}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                        placeholder="°F"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Glucose</label>
                      <input
                        type="number"
                        name="glucose"
                        value={formData.glucose}
                        onChange={handleChange}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                        placeholder="mg/dL"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Assessment */}
              {activeSection === "assessment" && (
                <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
                  <h2 className="text-xl font-semibold mb-4">Assessment</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Level of Consciousness</label>
                      <select
                        name="level_of_consciousness"
                        value={formData.level_of_consciousness}
                        onChange={handleChange}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                      >
                        <option value="">Select...</option>
                        <option value="alert">Alert</option>
                        <option value="verbal">Responds to Verbal</option>
                        <option value="painful">Responds to Painful</option>
                        <option value="unresponsive">Unresponsive</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Assessment Findings</label>
                      <textarea
                        name="assessment_findings"
                        value={formData.assessment_findings}
                        onChange={handleChange}
                        rows={6}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                        placeholder="Document physical exam findings, SAMPLE history, etc."
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Interventions */}
              {activeSection === "interventions" && (
                <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
                  <h2 className="text-xl font-semibold mb-4">Interventions</h2>
                  <div>
                    <label className="block text-sm font-medium mb-2">Interventions Performed</label>
                    <textarea
                      name="interventions"
                      value={formData.interventions}
                      onChange={handleChange}
                      rows={8}
                      className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                      placeholder="Document all procedures, treatments, and interventions (e.g., oxygen therapy, IV access, CPR, AED)"
                    />
                  </div>
                </div>
              )}

              {/* Medications */}
              {activeSection === "medications" && (
                <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
                  <h2 className="text-xl font-semibold mb-4">Medications</h2>
                  <div>
                    <label className="block text-sm font-medium mb-2">Medications Administered</label>
                    <textarea
                      name="medications"
                      value={formData.medications}
                      onChange={handleChange}
                      rows={8}
                      className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                      placeholder="Document medication name, dose, route, time (e.g., Aspirin 325mg PO 14:30)"
                    />
                  </div>
                </div>
              )}

              {/* Narrative */}
              {activeSection === "narrative" && (
                <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
                  <h2 className="text-xl font-semibold mb-4">Narrative</h2>
                  <div>
                    <label className="block text-sm font-medium mb-2">Patient Care Narrative *</label>
                    <NarrativeWithDictation
                      value={formData.narrative}
                      onChange={(text) => setFormData((prev) => ({ ...prev, narrative: text }))}
                      required
                      append
                    />
                  </div>
                </div>
              )}

              {/* Disposition */}
              {activeSection === "disposition" && (
                <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
                  <h2 className="text-xl font-semibold mb-4">Disposition</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Disposition *</label>
                      <select
                        name="disposition"
                        value={formData.disposition}
                        onChange={handleChange}
                        required
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                      >
                        <option value="">Select...</option>
                        <option value="transported">Transported</option>
                        <option value="refused">Refused Care</option>
                        <option value="cancelled">Cancelled</option>
                        <option value="dead_on_scene">Dead on Scene</option>
                        <option value="no_patient">No Patient Found</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Destination Facility</label>
                      <input
                        type="text"
                        name="destination_facility"
                        value={formData.destination_facility}
                        onChange={handleChange}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 focus:outline-none focus:border-blue-500"
                        placeholder="e.g., County General Hospital"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Form Actions */}
              <div className="flex justify-between items-center pt-6 border-t border-zinc-800">
                <button
                  type="button"
                  onClick={() => router.back()}
                  className="px-6 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={loading}
                    className="px-6 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg transition-colors disabled:opacity-50"
                  >
                    Save as Draft
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors font-medium disabled:opacity-50"
                  >
                    {loading ? "Saving..." : "Submit PCR"}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
