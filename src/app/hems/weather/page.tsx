"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { Cloud, AlertTriangle, Wind, Eye, ThermometerSun, Droplets } from "lucide-react";

type WeatherData = {
  current_conditions: {
    temperature: number;
    wind_speed: number;
    wind_direction: number;
    visibility: number;
    ceiling: number;
    conditions: string;
    flight_category: string;
  };
  minimums: {
    vfr_ceiling: number;
    vfr_visibility: number;
    ifr_ceiling: number;
    ifr_visibility: number;
    max_wind_speed: number;
  };
  decision_log: Array<{
    id: number;
    timestamp: string;
    decision: string;
    weather_conditions: string;
    pilot: string;
    justification: string;
  }>;
};

export default function WeatherPage() {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newDecision, setNewDecision] = useState({ decision: "", justification: "" });

  useEffect(() => {
    apiFetch<WeatherData>("/hems/weather", { credentials: "include" })
      .then(setWeather)
      .catch(() => setError("Failed to load weather data"))
      .finally(() => setLoading(false));
  }, []);

  const handleLogDecision = async () => {
    if (!newDecision.decision || !newDecision.justification) {
      alert("Please fill in all fields");
      return;
    }
    try {
      await apiFetch("/hems/weather/decision", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newDecision),
      });
      setNewDecision({ decision: "", justification: "" });
      window.location.reload();
    } catch (err) {
      alert("Failed to log decision");
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'vfr': return 'bg-green-500/20 text-green-400 border-green-500/50';
      case 'mvfr': return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
      case 'ifr': return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
      case 'lifr': return 'bg-red-500/20 text-red-400 border-red-500/50';
      default: return 'bg-zinc-700/20 text-zinc-400 border-zinc-700/50';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <Cloud className="w-12 h-12 text-teal-400 animate-pulse" />
      </div>
    );
  }

  if (error || !weather) {
    return (
      <div className="min-h-screen bg-zinc-950 p-6">
        <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 text-red-400">
          {error || "Weather data not available"}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="bg-gradient-to-r from-teal-950 via-zinc-900 to-emerald-950 border-b border-teal-900/30 px-6 py-8">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-teal-500 to-emerald-500 rounded-xl">
              <Cloud className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-zinc-100">Weather Minimums</h1>
              <p className="text-zinc-400">Weather conditions and go/no-go decision log</p>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Current Conditions */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-zinc-100">Current Conditions</h2>
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getCategoryColor(weather.current_conditions.flight_category)}`}>
              {weather.current_conditions.flight_category}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <div className="bg-zinc-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <ThermometerSun className="w-5 h-5 text-orange-400" />
                <span className="text-sm text-zinc-500">Temperature</span>
              </div>
              <div className="text-2xl font-bold text-zinc-100">{weather.current_conditions.temperature}°F</div>
            </div>

            <div className="bg-zinc-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Wind className="w-5 h-5 text-sky-400" />
                <span className="text-sm text-zinc-500">Wind</span>
              </div>
              <div className="text-2xl font-bold text-zinc-100">{weather.current_conditions.wind_speed} kts</div>
              <div className="text-xs text-zinc-500">{weather.current_conditions.wind_direction}°</div>
            </div>

            <div className="bg-zinc-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Eye className="w-5 h-5 text-teal-400" />
                <span className="text-sm text-zinc-500">Visibility</span>
              </div>
              <div className="text-2xl font-bold text-zinc-100">{weather.current_conditions.visibility} mi</div>
            </div>

            <div className="bg-zinc-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Cloud className="w-5 h-5 text-zinc-400" />
                <span className="text-sm text-zinc-500">Ceiling</span>
              </div>
              <div className="text-2xl font-bold text-zinc-100">{weather.current_conditions.ceiling} ft</div>
            </div>

            <div className="bg-zinc-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Droplets className="w-5 h-5 text-blue-400" />
                <span className="text-sm text-zinc-500">Conditions</span>
              </div>
              <div className="text-sm font-semibold text-zinc-100">{weather.current_conditions.conditions}</div>
            </div>
          </div>
        </motion.div>

        {/* Weather Minimums */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-xl font-bold text-zinc-100 mb-4">Company Weather Minimums</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-zinc-800 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-green-400 mb-3">VFR Minimums</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Ceiling:</span>
                  <span className="text-zinc-100">{weather.minimums.vfr_ceiling} ft AGL</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Visibility:</span>
                  <span className="text-zinc-100">{weather.minimums.vfr_visibility} mi</span>
                </div>
              </div>
            </div>

            <div className="bg-zinc-800 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-amber-400 mb-3">IFR Minimums</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-zinc-500">Ceiling:</span>
                  <span className="text-zinc-100">{weather.minimums.ifr_ceiling} ft AGL</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-500">Visibility:</span>
                  <span className="text-zinc-100">{weather.minimums.ifr_visibility} mi</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
            <div className="flex items-center gap-2 text-red-400">
              <AlertTriangle className="w-5 h-5" />
              <span className="font-semibold">Maximum Wind Speed: {weather.minimums.max_wind_speed} kts</span>
            </div>
          </div>
        </motion.div>

        {/* Log New Decision */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-xl font-bold text-zinc-100 mb-4">Log Go/No-Go Decision</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-zinc-400 mb-2">Decision</label>
              <select
                value={newDecision.decision}
                onChange={(e) => setNewDecision({ ...newDecision, decision: e.target.value })}
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-teal-500"
              >
                <option value="">Select decision...</option>
                <option value="go">GO - Flight Approved</option>
                <option value="no_go">NO-GO - Flight Declined</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-zinc-400 mb-2">Justification</label>
              <textarea
                value={newDecision.justification}
                onChange={(e) => setNewDecision({ ...newDecision, justification: e.target.value })}
                className="w-full h-24 px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 focus:outline-none focus:border-teal-500"
                placeholder="Enter decision justification..."
              />
            </div>
            <button
              onClick={handleLogDecision}
              className="w-full px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-semibold"
            >
              Log Decision
            </button>
          </div>
        </motion.div>

        {/* Decision Log */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h2 className="text-xl font-bold text-zinc-100 mb-4">Decision History</h2>
          <div className="space-y-3">
            {weather.decision_log.map((log) => (
              <div key={log.id} className="bg-zinc-800 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className={`px-2 py-1 rounded text-xs font-semibold ${
                    log.decision === 'go' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                  }`}>
                    {log.decision === 'go' ? 'GO' : 'NO-GO'}
                  </div>
                  <div className="text-xs text-zinc-500">{new Date(log.timestamp).toLocaleString()}</div>
                </div>
                <div className="text-sm text-zinc-400 mb-2">{log.weather_conditions}</div>
                <div className="text-sm text-zinc-300 mb-2">{log.justification}</div>
                <div className="text-xs text-zinc-500">Pilot: {log.pilot}</div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
