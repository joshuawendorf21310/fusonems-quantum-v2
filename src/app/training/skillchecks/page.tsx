"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  CheckCircle,
  XCircle,
  Clock,
  Award,
  User,
  Calendar,
  Filter,
  Download,
} from "lucide-react";

interface SkillCheck {
  id: number;
  skill_name: string;
  personnel_id: number;
  personnel_name: string;
  evaluator_name: string;
  check_date: string;
  passed: boolean;
  score: number | null;
  notes: string;
  next_check_date: string | null;
}

export default function SkillChecksPage() {
  const [skillChecks, setSkillChecks] = useState<SkillCheck[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    fetchSkillChecks();
  }, [filter]);

  const fetchSkillChecks = async () => {
    try {
      const params = new URLSearchParams();
      if (filter !== "all") params.set("status", filter);

      const res = await fetch(`/api/training/skill-checks?${params}`, {
        credentials: "include",
      });

      if (res.ok) {
        setSkillChecks(await res.json());
      }
    } catch (error) {
      console.error("Error fetching skill checks:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-between items-center"
        >
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
              Skill Check-Offs
            </h1>
            <p className="text-zinc-400 mt-2">Track and verify personnel skills</p>
          </div>
          <div className="flex gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg hover:bg-zinc-700 flex items-center gap-2"
            >
              <Filter size={20} />
              Filter
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-lg flex items-center gap-2"
            >
              <Download size={20} />
              Export
            </motion.button>
          </div>
        </motion.div>

        {/* Filter Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex gap-2"
        >
          {["all", "passed", "failed", "pending"].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-6 py-3 rounded-lg font-medium capitalize transition-all ${
                filter === status
                  ? "bg-gradient-to-r from-blue-600 to-emerald-600"
                  : "bg-zinc-800 hover:bg-zinc-700"
              }`}
            >
              {status}
            </button>
          ))}
        </motion.div>

        {/* Skill Checks Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-6"
        >
          {skillChecks.length === 0 ? (
            <div className="col-span-2 bg-zinc-900 border border-zinc-800 rounded-xl p-12 text-center">
              <Award size={64} className="mx-auto mb-4 text-zinc-600" />
              <p className="text-zinc-500">No skill checks found</p>
            </div>
          ) : (
            skillChecks.map((check, idx) => (
              <motion.div
                key={check.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + idx * 0.05 }}
                className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-bold mb-2">{check.skill_name}</h3>
                    <div className="flex items-center gap-2 text-sm text-zinc-400">
                      <User size={16} />
                      {check.personnel_name}
                    </div>
                  </div>
                  <div
                    className={`p-3 rounded-xl ${
                      check.passed
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-red-500/20 text-red-400"
                    }`}
                  >
                    {check.passed ? <CheckCircle size={24} /> : <XCircle size={24} />}
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-zinc-400">Evaluator</span>
                    <span className="font-medium">{check.evaluator_name}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-zinc-400">Check Date</span>
                    <span className="font-medium">
                      {new Date(check.check_date).toLocaleDateString()}
                    </span>
                  </div>
                  {check.score !== null && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-zinc-400">Score</span>
                      <span className="font-bold text-lg">{check.score}%</span>
                    </div>
                  )}
                  {check.next_check_date && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-zinc-400">Next Check</span>
                      <span className="font-medium flex items-center gap-2">
                        <Calendar size={14} />
                        {new Date(check.next_check_date).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>

                {check.notes && (
                  <div className="mt-4 pt-4 border-t border-zinc-800">
                    <p className="text-sm text-zinc-400">{check.notes}</p>
                  </div>
                )}
              </motion.div>
            ))
          )}
        </motion.div>
      </div>
    </div>
  );
}
