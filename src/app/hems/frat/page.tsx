"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { AlertTriangle, Save, Calculator } from "lucide-react";

type FRATSection = {
  name: string;
  questions: Array<{
    id: string;
    question: string;
    options: Array<{ label: string; points: number }>;
  }>;
};

const fratSections: FRATSection[] = [
  {
    name: "Weather",
    questions: [
      {
        id: "weather_ceiling",
        question: "Ceiling (AGL)",
        options: [
          { label: "3000+ ft", points: 0 },
          { label: "1000-2999 ft", points: 2 },
          { label: "500-999 ft", points: 4 },
          { label: "Below 500 ft", points: 6 },
        ],
      },
      {
        id: "weather_visibility",
        question: "Visibility",
        options: [
          { label: "5+ miles", points: 0 },
          { label: "3-4 miles", points: 2 },
          { label: "1-2 miles", points: 4 },
          { label: "Below 1 mile", points: 6 },
        ],
      },
      {
        id: "weather_wind",
        question: "Wind Speed",
        options: [
          { label: "0-15 kts", points: 0 },
          { label: "16-25 kts", points: 2 },
          { label: "26-35 kts", points: 4 },
          { label: "Above 35 kts", points: 6 },
        ],
      },
    ],
  },
  {
    name: "Flight Environment",
    questions: [
      {
        id: "time_of_day",
        question: "Time of Day",
        options: [
          { label: "Day", points: 0 },
          { label: "Dusk/Dawn", points: 2 },
          { label: "Night", points: 4 },
        ],
      },
      {
        id: "terrain",
        question: "Terrain",
        options: [
          { label: "Flat, open", points: 0 },
          { label: "Rolling hills", points: 2 },
          { label: "Mountains", points: 4 },
          { label: "Obstacles/wires", points: 6 },
        ],
      },
      {
        id: "landing_zone",
        question: "Landing Zone Familiarity",
        options: [
          { label: "Familiar, prepared LZ", points: 0 },
          { label: "Previously used, unprepared", points: 2 },
          { label: "Unfamiliar, unprepared", points: 4 },
        ],
      },
    ],
  },
  {
    name: "Pilot Factors",
    questions: [
      {
        id: "pilot_experience",
        question: "Pilot Total Hours",
        options: [
          { label: "2000+ hours", points: 0 },
          { label: "1000-1999 hours", points: 1 },
          { label: "500-999 hours", points: 2 },
          { label: "Below 500 hours", points: 3 },
        ],
      },
      {
        id: "pilot_fatigue",
        question: "Pilot Fatigue",
        options: [
          { label: "Well rested", points: 0 },
          { label: "Somewhat tired", points: 2 },
          { label: "Fatigued", points: 4 },
        ],
      },
      {
        id: "pilot_stress",
        question: "Pilot Stress Level",
        options: [
          { label: "Low stress", points: 0 },
          { label: "Moderate stress", points: 2 },
          { label: "High stress", points: 4 },
        ],
      },
    ],
  },
  {
    name: "Mission Factors",
    questions: [
      {
        id: "mission_urgency",
        question: "Mission Urgency",
        options: [
          { label: "Routine transport", points: 0 },
          { label: "Time-sensitive", points: 2 },
          { label: "Life-threatening emergency", points: 4 },
        ],
      },
      {
        id: "mission_distance",
        question: "Mission Distance",
        options: [
          { label: "Under 50 nm", points: 0 },
          { label: "50-100 nm", points: 1 },
          { label: "Over 100 nm", points: 2 },
        ],
      },
    ],
  },
];

export default function FRATPage() {
  const [responses, setResponses] = useState<Record<string, number>>({});
  const [saving, setSaving] = useState(false);
  const [mission, setMission] = useState({ mission_number: "", pilot: "" });

  const totalScore = Object.values(responses).reduce((sum, val) => sum + val, 0);

  const getRiskLevel = (score: number) => {
    if (score < 20) return { level: "LOW", color: "green", message: "Flight approved under standard procedures" };
    if (score < 40) return { level: "MODERATE", color: "amber", message: "Flight requires supervisor approval" };
    return { level: "HIGH", color: "red", message: "Flight requires chief pilot approval and risk mitigation" };
  };

  const risk = getRiskLevel(totalScore);

  const handleSave = async () => {
    if (!mission.mission_number || !mission.pilot) {
      alert("Please enter mission number and pilot");
      return;
    }

    setSaving(true);
    try {
      await apiFetch("/hems/frat", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mission_number: mission.mission_number,
          pilot: mission.pilot,
          responses,
          total_score: totalScore,
          risk_level: risk.level,
        }),
      });
      alert("FRAT assessment saved successfully");
      setResponses({});
      setMission({ mission_number: "", pilot: "" });
    } catch (err) {
      alert("Failed to save FRAT assessment");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="bg-gradient-to-r from-amber-950 via-zinc-900 to-orange-950 border-b border-amber-900/30 px-6 py-8">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl">
              <AlertTriangle className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-zinc-100">Flight Risk Assessment Tool (FRAT)</h1>
              <p className="text-zinc-400">Systematic pre-flight risk evaluation</p>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="p-6 max-w-5xl mx-auto space-y-6">
        {/* Mission Info */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-xl font-bold text-zinc-100 mb-4">Mission Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-zinc-400 mb-2">Mission Number</label>
              <input
                type="text"
                value={mission.mission_number}
                onChange={(e) => setMission({ ...mission, mission_number: e.target.value })}
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-amber-500"
                placeholder="Enter mission number"
              />
            </div>
            <div>
              <label className="block text-sm text-zinc-400 mb-2">Pilot in Command</label>
              <input
                type="text"
                value={mission.pilot}
                onChange={(e) => setMission({ ...mission, pilot: e.target.value })}
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-amber-500"
                placeholder="Enter pilot name"
              />
            </div>
          </div>
        </motion.div>

        {/* FRAT Sections */}
        {fratSections.map((section, sectionIdx) => (
          <motion.div
            key={section.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + sectionIdx * 0.1 }}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-6"
          >
            <h2 className="text-xl font-bold text-zinc-100 mb-4">{section.name}</h2>
            <div className="space-y-4">
              {section.questions.map((q) => (
                <div key={q.id} className="bg-zinc-800 rounded-lg p-4">
                  <div className="text-sm font-semibold text-zinc-200 mb-3">{q.question}</div>
                  <div className="space-y-2">
                    {q.options.map((option) => (
                      <label key={option.label} className="flex items-center gap-3 p-2 rounded hover:bg-zinc-700 cursor-pointer transition-colors">
                        <input
                          type="radio"
                          name={q.id}
                          value={option.points}
                          checked={responses[q.id] === option.points}
                          onChange={() => setResponses({ ...responses, [q.id]: option.points })}
                          className="w-4 h-4 text-amber-500 focus:ring-amber-500"
                        />
                        <span className="text-sm text-zinc-300 flex-1">{option.label}</span>
                        <span className="text-xs text-zinc-500 font-mono">{option.points} pts</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        ))}

        {/* Score Summary */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className={`border-2 rounded-xl p-6 ${
            risk.color === "green"
              ? "bg-green-500/10 border-green-500"
              : risk.color === "amber"
              ? "bg-amber-500/10 border-amber-500"
              : "bg-red-500/10 border-red-500"
          }`}
        >
          <div className="flex items-center gap-4 mb-4">
            <Calculator className={`w-8 h-8 text-${risk.color}-400`} />
            <div>
              <h2 className="text-2xl font-bold text-zinc-100">Risk Assessment Result</h2>
              <p className="text-zinc-400">Total score calculated from responses</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-zinc-900/50 rounded-lg p-4 text-center">
              <div className="text-sm text-zinc-500 mb-1">Total Score</div>
              <div className={`text-5xl font-bold text-${risk.color}-400`}>{totalScore}</div>
            </div>
            <div className="bg-zinc-900/50 rounded-lg p-4 text-center">
              <div className="text-sm text-zinc-500 mb-1">Risk Level</div>
              <div className={`text-3xl font-bold text-${risk.color}-400`}>{risk.level}</div>
            </div>
            <div className="bg-zinc-900/50 rounded-lg p-4 flex items-center justify-center">
              <AlertTriangle className={`w-16 h-16 text-${risk.color}-400`} />
            </div>
          </div>

          <div className={`p-4 rounded-lg bg-${risk.color}-500/20 border border-${risk.color}-500/50`}>
            <p className={`text-${risk.color}-400 font-semibold`}>{risk.message}</p>
          </div>
        </motion.div>

        {/* Save Button */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }}>
          <button
            onClick={handleSave}
            disabled={saving || Object.keys(responses).length === 0}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-amber-600 hover:bg-amber-700 disabled:bg-zinc-700 text-white rounded-lg font-semibold text-lg transition-colors"
          >
            <Save className="w-6 h-6" />
            {saving ? "Saving..." : "Save FRAT Assessment"}
          </button>
        </motion.div>

        {/* Scoring Guide */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-xl font-bold text-zinc-100 mb-4">Scoring Guide</h2>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-3 p-2 bg-green-500/10 border border-green-500/30 rounded">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
              <span className="text-zinc-300"><strong className="text-green-400">Low Risk (0-19):</strong> Flight approved under standard procedures</span>
            </div>
            <div className="flex items-center gap-3 p-2 bg-amber-500/10 border border-amber-500/30 rounded">
              <div className="w-3 h-3 bg-amber-500 rounded-full" />
              <span className="text-zinc-300"><strong className="text-amber-400">Moderate Risk (20-39):</strong> Flight requires operations supervisor approval</span>
            </div>
            <div className="flex items-center gap-3 p-2 bg-red-500/10 border border-red-500/30 rounded">
              <div className="w-3 h-3 bg-red-500 rounded-full" />
              <span className="text-zinc-300"><strong className="text-red-400">High Risk (40+):</strong> Flight requires chief pilot approval and risk mitigation plan</span>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
