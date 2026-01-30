"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Clock,
  Target,
  TrendingUp,
  Award,
  AlertCircle,
  CheckCircle2,
  XCircle,
  BarChart3,
  Calendar,
  Play,
} from "lucide-react";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from "recharts";

export default function AssessmentsCenter() {
  const [selectedCategory, setSelectedCategory] = useState("all");

  const upcomingTests = [
    {
      id: 1,
      title: "ACLS Final Exam",
      course: "Advanced Cardiac Life Support",
      dueDate: "Jan 31, 2026",
      daysLeft: 3,
      duration: "60 min",
      questions: 50,
      passingScore: 80,
      attempts: 2,
      status: "due-soon",
    },
    {
      id: 2,
      title: "Trauma Assessment Quiz",
      course: "Trauma Assessment & Management",
      dueDate: "Feb 3, 2026",
      daysLeft: 6,
      duration: "30 min",
      questions: 25,
      passingScore: 80,
      attempts: 3,
      status: "upcoming",
    },
  ];

  const practiceTests = [
    {
      id: 1,
      title: "ACLS Practice Test",
      questions: 50,
      duration: "60 min",
      attempts: 5,
      bestScore: 92,
      lastAttempt: "2 days ago",
    },
    {
      id: 2,
      title: "PALS Practice Exam",
      questions: 40,
      duration: "45 min",
      attempts: 3,
      bestScore: 88,
      lastAttempt: "1 week ago",
    },
    {
      id: 3,
      title: "Trauma Scenarios",
      questions: 20,
      duration: "30 min",
      attempts: 8,
      bestScore: 95,
      lastAttempt: "Yesterday",
    },
  ];

  const recentScores = [
    {
      id: 1,
      title: "PALS Final Exam",
      date: "Jan 15, 2026",
      score: 98,
      status: "passed",
      questions: 40,
      timeSpent: "42 min",
    },
    {
      id: 2,
      title: "BLS Recertification",
      date: "Jan 8, 2026",
      score: 95,
      status: "passed",
      questions: 30,
      timeSpent: "28 min",
    },
    {
      id: 3,
      title: "Hazmat Operations Quiz",
      date: "Dec 28, 2025",
      score: 100,
      status: "passed",
      questions: 25,
      timeSpent: "22 min",
    },
  ];

  const skillCheckoffs = [
    {
      id: 1,
      skill: "Endotracheal Intubation",
      level: "Advanced",
      status: "certified",
      expiry: "Jun 2026",
      signedBy: "Dr. Sarah Mitchell",
    },
    {
      id: 2,
      skill: "IV Therapy",
      level: "Advanced",
      status: "certified",
      expiry: "May 2026",
      signedBy: "Lt. Mike Rodriguez",
    },
    {
      id: 3,
      skill: "12-Lead EKG",
      level: "Intermediate",
      status: "pending",
      expiry: null,
      signedBy: null,
    },
    {
      id: 4,
      skill: "Trauma Assessment",
      level: "Advanced",
      status: "expiring-soon",
      expiry: "Feb 2026",
      signedBy: "Dr. James Wilson",
    },
  ];

  const performanceData = [
    { category: "Clinical", score: 92 },
    { category: "Operations", score: 88 },
    { category: "Leadership", score: 85 },
    { category: "Safety", score: 95 },
    { category: "Communication", score: 90 },
  ];

  const scoreHistory = [
    { month: "Aug", score: 82 },
    { month: "Sep", score: 85 },
    { month: "Oct", score: 88 },
    { month: "Nov", score: 90 },
    { month: "Dec", score: 93 },
    { month: "Jan", score: 95 },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "due-soon":
        return "border-red-500 bg-red-500/10";
      case "upcoming":
        return "border-yellow-500 bg-yellow-500/10";
      case "passed":
        return "border-emerald-500 bg-emerald-500/10";
      case "certified":
        return "bg-emerald-500/20 text-emerald-400";
      case "pending":
        return "bg-yellow-500/20 text-yellow-400";
      case "expiring-soon":
        return "bg-orange-500/20 text-orange-400";
      default:
        return "border-slate-500 bg-slate-500/10";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            Assessments Center
          </h1>
          <p className="text-slate-400 mt-2">Track tests, scores, and skill competencies</p>
        </motion.div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-2xl p-6"
          >
            <Target className="mb-3" size={32} />
            <div className="text-4xl font-bold mb-1">95%</div>
            <p className="text-blue-100 text-sm">Average Score</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-emerald-600 to-emerald-800 rounded-2xl p-6"
          >
            <CheckCircle2 className="mb-3" size={32} />
            <div className="text-4xl font-bold mb-1">24</div>
            <p className="text-emerald-100 text-sm">Tests Passed</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-br from-orange-600 to-orange-800 rounded-2xl p-6"
          >
            <AlertCircle className="mb-3" size={32} />
            <div className="text-4xl font-bold mb-1">2</div>
            <p className="text-orange-100 text-sm">Upcoming Tests</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-gradient-to-br from-purple-600 to-purple-800 rounded-2xl p-6"
          >
            <TrendingUp className="mb-3" size={32} />
            <div className="text-4xl font-bold mb-1">+12%</div>
            <p className="text-purple-100 text-sm">Score Improvement</p>
          </motion.div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Radar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-2xl p-6"
            style={{ minWidth: 320, minHeight: 160 }}
          >
            <div className="flex items-center gap-2 mb-6">
              <BarChart3 size={24} />
              <h2 className="text-2xl font-bold">Performance by Category</h2>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={performanceData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="category" stroke="#94A3B8" />
                <PolarRadiusAxis stroke="#94A3B8" />
                <Radar
                  name="Score"
                  dataKey="score"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  fillOpacity={0.6}
                />
              </RadarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Score History */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-2xl p-6"
          >
            <div className="flex items-center gap-2 mb-6">
              <TrendingUp size={24} />
              <h2 className="text-2xl font-bold">Score Trends</h2>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={scoreHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="month" stroke="#94A3B8" />
                <YAxis stroke="#94A3B8" domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1E293B",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#10B981"
                  strokeWidth={3}
                  dot={{ fill: "#10B981", r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>
        </div>

        {/* Upcoming Tests */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-2xl p-6"
        >
          <div className="flex items-center gap-2 mb-6">
            <Clock size={24} />
            <h2 className="text-2xl font-bold">Upcoming Tests</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {upcomingTests.map((test, idx) => (
              <motion.div
                key={test.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.7 + idx * 0.1 }}
                className={`border-l-4 rounded-xl p-6 ${getStatusColor(test.status)}`}
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-bold text-xl mb-1">{test.title}</h3>
                    <p className="text-sm text-slate-400">{test.course}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-red-400">{test.daysLeft}</div>
                    <div className="text-xs text-slate-400">days left</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                  <div>
                    <div className="text-slate-400">Due Date</div>
                    <div className="font-semibold">{test.dueDate}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Duration</div>
                    <div className="font-semibold">{test.duration}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Questions</div>
                    <div className="font-semibold">{test.questions}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Passing</div>
                    <div className="font-semibold">{test.passingScore}%</div>
                  </div>
                </div>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full bg-gradient-to-r from-blue-600 to-emerald-600 py-3 rounded-xl font-semibold flex items-center justify-center gap-2"
                >
                  <Play size={18} />
                  Start Test
                </motion.button>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Practice Tests & Recent Scores */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Practice Tests */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-2xl p-6"
          >
            <div className="flex items-center gap-2 mb-6">
              <Target size={24} />
              <h2 className="text-2xl font-bold">Practice Tests</h2>
            </div>
            <div className="space-y-4">
              {practiceTests.map((test, idx) => (
                <motion.div
                  key={test.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.9 + idx * 0.1 }}
                  className="bg-slate-800/50 rounded-xl p-4 hover:bg-slate-800 transition-colors"
                >
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-semibold">{test.title}</h3>
                    <span className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded text-xs font-medium">
                      Best: {test.bestScore}%
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-slate-400 mb-3">
                    <div>{test.questions} questions</div>
                    <div>•</div>
                    <div>{test.duration}</div>
                    <div>•</div>
                    <div>{test.attempts} attempts</div>
                  </div>
                  <div className="text-xs text-slate-500 mb-3">Last: {test.lastAttempt}</div>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full bg-slate-700 hover:bg-slate-600 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    Practice Again
                  </motion.button>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Recent Scores */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-2xl p-6"
          >
            <div className="flex items-center gap-2 mb-6">
              <Award size={24} />
              <h2 className="text-2xl font-bold">Recent Scores</h2>
            </div>
            <div className="space-y-4">
              {recentScores.map((score, idx) => (
                <motion.div
                  key={score.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 1.0 + idx * 0.1 }}
                  className="bg-slate-800/50 rounded-xl p-4 border-l-4 border-emerald-500"
                >
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-semibold">{score.title}</h3>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-emerald-400">{score.score}%</div>
                      <CheckCircle2 className="inline text-emerald-400" size={16} />
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-slate-400">
                    <div>{score.date}</div>
                    <div>•</div>
                    <div>{score.questions} questions</div>
                    <div>•</div>
                    <div>{score.timeSpent}</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Skill Checkoffs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.1 }}
          className="bg-slate-900/50 backdrop-blur-lg border border-slate-800 rounded-2xl p-6"
        >
          <div className="flex items-center gap-2 mb-6">
            <CheckCircle2 size={24} />
            <h2 className="text-2xl font-bold">Skill Checkoffs</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {skillCheckoffs.map((skill, idx) => (
              <motion.div
                key={skill.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.2 + idx * 0.1 }}
                className="bg-slate-800/50 rounded-xl p-4"
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold mb-1">{skill.skill}</h3>
                    <span className="text-xs text-slate-400">{skill.level}</span>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                      skill.status
                    )}`}
                  >
                    {skill.status.replace("-", " ")}
                  </span>
                </div>
                {skill.status !== "pending" && (
                  <div className="text-sm text-slate-400">
                    <div>Expires: {skill.expiry}</div>
                    <div>Signed by: {skill.signedBy}</div>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
